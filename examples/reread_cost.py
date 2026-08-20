"""
Is re-reading a set of CSV files a rounding error in a polars streaming pipeline?

H0: reading the files a second time is a rounding error -- the two-pass pipeline
    finishes within M=10% of the single-pass pipeline on the same workload.
H1: the second read costs materially more than M, because parsing dominates the
    pipeline and a second pass pays for it twice.

M is committed before the run. "Rounding error" is unfalsifiable without a
margin: any measured difference can be waved through as noise after the fact.

The arms differ only in how many times the CSVs are parsed:
  one-pass  scan once, materialise once, validate and transform off that frame
  two-pass  scan and validate (streaming), then scan again, transform and sink

Each pass is also timed alone, plus a parse-only arm. The ratio between the arms
is machine-specific; the parse share of the pipeline is the part that travels.
If parsing dominates, no amount of tuning makes a second read free.

Run in a throwaway environment, not the project's:
    python -m venv /tmp/rrc && /tmp/rrc/bin/pip install polars
    /tmp/rrc/bin/python reread_cost.py
"""

import platform
import shutil
import statistics
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import polars as pl

N_FILES = 10
N_ROWS = 1_000_000
REPS = 7
WARMUP = 2
MARGIN = 0.10

COLS = ["id", "region", "qty", "unit_price", "recorded_at"]


def build_workload(dir: Path) -> int:
    """Deterministic CSVs, so every arm and every repetition parses identical bytes."""
    total = 0
    for f in range(N_FILES):
        pl.select(
            id=pl.int_range(f * N_ROWS, (f + 1) * N_ROWS, dtype=pl.Int64),
            region=pl.format("r{}", pl.int_range(0, N_ROWS).mod(7)),
            qty=pl.int_range(0, N_ROWS).mod(97) + 1,
            unit_price=(pl.int_range(0, N_ROWS).mod(1999) + 1).cast(pl.Float64) / 100,
            recorded_at=(
                pl.lit(datetime(2024, 1, 1))
                + pl.duration(seconds=pl.int_range(0, N_ROWS))
            ).dt.strftime("%Y-%m-%dT%H:%M:%S"),
        ).write_csv(dir / f"part_{f:02d}.csv")
        total += (dir / f"part_{f:02d}.csv").stat().st_size
    return total


def validation(scan: pl.LazyFrame) -> pl.LazyFrame:
    """Null counts per column plus range checks: touches every column."""
    return scan.select(
        [pl.col(c).null_count().alias(f"nulls_{c}") for c in COLS]
        + [
            pl.col("qty").min().alias("qty_min"),
            pl.col("qty").max().alias("qty_max"),
            pl.col("unit_price").min().alias("price_min"),
            pl.len().alias("rows"),
        ]
    )


def transform(scan: pl.LazyFrame) -> pl.LazyFrame:
    return (
        scan.with_columns(
            line_total=pl.col("qty") * pl.col("unit_price"),
            recorded_at=pl.col("recorded_at").str.to_datetime("%Y-%m-%dT%H:%M:%S"),
        )
        .group_by("region")
        .agg(revenue=pl.col("line_total").sum(), units=pl.col("qty").sum())
    )


def parse_only(src: Path, out: Path) -> None:
    pl.scan_csv(str(src / "*.csv")).collect(engine="streaming")


def one_pass(src: Path, out: Path) -> None:
    df = pl.scan_csv(str(src / "*.csv")).collect(engine="streaming")
    validation(df.lazy()).collect()
    transform(df.lazy()).collect().write_parquet(out)


def validate_pass(src: Path, out: Path) -> None:
    validation(pl.scan_csv(str(src / "*.csv"))).collect(engine="streaming")


def transform_pass(src: Path, out: Path) -> None:
    transform(pl.scan_csv(str(src / "*.csv"))).sink_parquet(out)


def two_pass(src: Path, out: Path) -> None:
    validate_pass(src, out)
    transform_pass(src, out)


def measure(fn, src: Path, out: Path) -> list[float]:
    for _ in range(WARMUP):
        fn(src, out)
    times = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        fn(src, out)
        times.append(time.perf_counter() - t0)
    return times


def report(label: str, times: list[float]) -> float:
    med = statistics.median(times)
    spread = (max(times) - min(times)) / med
    print(f"{label:<15} median {med:7.3f}s   min {min(times):7.3f}s   "
          f"max {max(times):7.3f}s   spread {spread:5.1%}")
    return med


print("=== environment ===")
print(f"python   : {sys.version.split()[0]} ({platform.python_implementation()})")
print(f"polars   : {pl.__version__}")
print(f"platform : {platform.platform()}")
print(f"machine  : {platform.processor() or platform.machine()}")
print()

tmp = Path(tempfile.mkdtemp(prefix="reread-"))
try:
    src = tmp / "src"
    src.mkdir()
    nbytes = build_workload(src)
    out = tmp / "out.parquet"

    print("=== workload ===")
    print(f"files    : {N_FILES} CSV, {N_ROWS:,} rows each "
          f"({N_FILES * N_ROWS:,} rows total)")
    print(f"on disk  : {nbytes / 1e6:.1f} MB")
    print(f"reps     : {REPS} timed, {WARMUP} discarded as warmup")
    print(f"margin M : {MARGIN:.0%}, committed before the run")
    print("note     : files were just written, so they are in the OS page cache. "
          "This measures\n           parse cost with no disk I/O -- the most "
          "favourable case for a second read.")
    print()

    print("=== floor control: moving the bytes with no parsing ===")
    paths = sorted(src.glob("*.csv"))
    for _ in range(WARMUP):
        for p in paths:
            p.read_bytes()
    t0 = time.perf_counter()
    for p in paths:
        p.read_bytes()
    raw = time.perf_counter() - t0
    print(f"raw byte read   {raw:7.3f}s   ({nbytes / raw / 1e9:.2f} GB/s)")
    print()

    print("=== measured ===")
    m_parse = report("parse only", measure(parse_only, src, out))
    m_one = report("one-pass", measure(one_pass, src, out))
    m_two = report("two-pass", measure(two_pass, src, out))
    m_val = report("validate only", measure(validate_pass, src, out))
    m_tra = report("transform only", measure(transform_pass, src, out))
    print()
    print(f"parse / floor   {m_parse / raw:7.2f}x   "
          f"(sanity check: parsing must cost more than copying)")
    print()

    print("=== observed ===")
    overhead = (m_two - m_one) / m_one
    print(f"two-pass / one-pass  : {m_two / m_one:.2f}x  ({overhead:+.1%})")
    print(f"margin M             : {MARGIN:+.1%}")
    print(f"within margin?       : {overhead <= MARGIN}")
    print()
    print(f"parse share of one-pass  : {m_parse / m_one:.1%}")
    print(f"marginal cost of pass 2  : {m_two - m_one:.3f}s")
    print()
    print("consistency check -- the two-pass arm should be its two passes and nothing else:")
    print(f"  validate + transform   : {m_val + m_tra:.3f}s")
    print(f"  two-pass measured      : {m_two:.3f}s")
finally:
    shutil.rmtree(tmp)
