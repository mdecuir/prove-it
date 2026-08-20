# Worked example: is this cost negligible?

This one started as a planning assumption rather than a library fact, which is the more
common and more expensive case. The shape of the problem is generic:

> You are designing a pipeline that reads a set of CSV files, validates the data in them,
> computes derived values, and writes the result somewhere new. There is a fork in the
> design. Either fuse the work into a single read — validate and generate output in one
> streaming pass — or keep the two concerns separate: read once to validate, then read
> again to produce the output. The second is much easier to reason about and to test.
>
> The assertion made in favour of it was that **re-reading the files would be a rounding
> error** against the rest of the pipeline's cost.

That is a performance claim wearing the clothes of an architectural aside, which is why it
was worth stopping on. It sounds too small to check, it decides the structure of the code,
and nobody re-examines it once the code exists.

---

## Claim

Re-reading a set of CSV files for a second pass is a rounding error in the total cost of a
polars streaming pipeline that validates and then transforms them.

## Hypotheses

**H₀:** the two-pass pipeline finishes within **M = 10%** of the single-pass pipeline on
the same workload.

**H₁:** the second read costs materially more than M, because parsing dominates the
pipeline and a second pass pays for it twice.

**H₀ rejected if:** the two-pass median exceeds the one-pass median by more than 10%.

M has to be committed before the run or the claim is not falsifiable at all. "Rounding
error" has no fixed meaning, so any measured difference can be waved through as noise
afterwards — which is exactly how an assumption like this survives being checked. Naming
10% first is what turns it into a claim that can lose.

## Experiment

[`reread_cost.py`](./reread_cost.py). Two arms over identical, deterministically generated
files, differing only in how many times the CSVs are parsed: one arm scans once and does
both jobs off the materialised frame, the other scans and validates in streaming mode, then
scans again to transform and sink.

Three things in the harness exist to keep the number honest:

- **A floor control.** Reading the same bytes with no parsing at all, to establish the
  fastest the machine can even move the data. A parse that came out faster than a raw
  byte copy would mean the arm was not reading what it claimed to.
- **Each pass timed alone,** so the total can be checked against the sum of its parts. If
  they disagreed, something — caching between passes, a shared plan — would be happening
  that the two-arm comparison alone could not see.
- **A parse-only arm,** because the ratio between the two arms is a fact about this
  machine, while the *share* of the pipeline spent parsing is the part that generalises.

Median of 7 timed repetitions, 2 discarded as warmup, spread reported alongside.

## Raw output

```
=== environment ===
python   : 3.14.7 (CPython)
polars   : 1.43.2
platform : macOS-26.5.2-arm64-arm-64bit-Mach-O
machine  : arm

=== workload ===
files    : 10 CSV, 1,000,000 rows each (10,000,000 rows total)
on disk  : 409.7 MB
reps     : 7 timed, 2 discarded as warmup
margin M : 10%, committed before the run
note     : files were just written, so they are in the OS page cache. This measures
           parse cost with no disk I/O -- the most favourable case for a second read.

=== floor control: moving the bytes with no parsing ===
raw byte read     0.021s   (19.49 GB/s)

=== measured ===
parse only      median   0.075s   min   0.074s   max   0.077s   spread  4.0%
one-pass        median   0.088s   min   0.085s   max   0.090s   spread  5.7%
two-pass        median   0.135s   min   0.133s   max   0.141s   spread  6.0%
validate only   median   0.072s   min   0.068s   max   0.075s   spread  9.2%
transform only  median   0.063s   min   0.061s   max   0.064s   spread  4.4%

parse / floor      3.55x   (sanity check: parsing must cost more than copying)

=== observed ===
two-pass / one-pass  : 1.54x  (+54.3%)
margin M             : +10.0%
within margin?       : False

parse share of one-pass  : 85.0%
marginal cost of pass 2  : 0.048s

consistency check -- the two-pass arm should be its two passes and nothing else:
  validate + transform   : 0.135s
  two-pass measured      : 0.135s
```

## Verdict

**Refuted**, on this workload and machine.

**H₀ was:** the two-pass pipeline finishes within M = 10% of the single-pass pipeline on
the same workload.
**Observed:** two-pass median 0.135s against one-pass median 0.088s — **+54%**, over five
times the committed margin, with both compared arms' spread at 6% or less.
**Now believed:** H₁, and the parse-share measurement explains the mechanism it predicted.

The reread is not a rounding error, and the parse share says why. Parsing is **85%** of the
single-pass pipeline, so the pipeline essentially *is* the read — validation and
transformation are the cheap parts. Paying the dominant cost twice cannot be marginal, and
this holds regardless of the absolute numbers on any particular machine.

Two things make the result stronger than the headline figure rather than weaker:

The files had just been written, so they were in the OS page cache and no disk I/O was
involved. That is the **most favourable possible case for a second read**. On cold cache,
network storage, or anything larger than RAM, the second pass gets worse, not better.

The consistency check came out exact — validate plus transform measured separately is the
same as the two-pass arm measured as a unit. Polars is not quietly reusing anything between
the passes, so the second read is a genuine second read.

## Consequences

The design choice does not get made on this basis. If the two concerns are kept separate,
that has to be justified by clarity and testability, knowing it costs roughly half again in
wall-clock — which may well be the right trade, but it is now a trade rather than a freebie.

Scoped narrowly, and the scope points at the actual fix: **this is a claim about CSV, not
about re-reading.** CSV parsing is expensive because the format is row-oriented text with
no schema. The same experiment against Parquet would very likely give a different verdict —
columnar, compressed, typed, and subject to projection pushdown, so a validation pass that
touches four columns reads only those four. Converting on ingest would attack the 85%
directly instead of arguing about how many times to pay it. That is the follow-up
experiment, and it is a different one.

---

## Why this example

**The harness was wrong twice, and both corrections are in the history rather than hidden.**

The first run reported 15ms to parse 64MB, which is not physically plausible, and the
initial instinct was to accept it — the arms compared cleanly and the ratio looked
reasonable. What settled it was the floor control: raw page-cached reads ran at 19 GB/s and
polars parsed at 3.5× that cost, which is internally consistent. The machine was simply
fast and the workload was too small. Nothing was wrong except the size of the input, and
without the floor measurement there was no way to tell that from a broken arm.

The second was a derived statistic — "parse share of the two-pass arm" — that printed
**109%**. It was comparing a materialising `collect()` against streaming passes that never
build the full frame, so it was measuring two different things and dividing them. A number
over 100% is obvious enough to catch. The same mistake at 40% would have been reported as a
finding.

**An unpredicted result worth keeping:** the transform pass alone (parse, group-by, and
Parquet write) is *cheaper* than the parse-only arm, because the streaming group-by never
materialises the full frame while `collect()` does. "The cost of reading the files" is not
one number — it depends on what the query plan does downstream with them.
