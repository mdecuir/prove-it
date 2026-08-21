# Worked example: is a shared `itertools.count()` thread-safe?

**Claim, as stated:** "`itertools.count()` is thread-safe, so a single counter can be shared
across worker threads."

**Claim type:** concurrency — the category where clean output is worth the least.
**Verdict:** **Refuted**, for CPython 3.14.7 with the GIL enabled.

This example is here for the harness, not the answer. A concurrency claim is the one place
where a green result carries almost no information: H₀ ("it's safe") and H₁ ("it's safe by
accident, on one code path") predict the same clean output on every input a confirming test
would reach for. So the work is nearly all in proving the *instrument* can see a race at all,
and then finding the input where the two hypotheses diverge.

Three separate harness defects were caught here before any result was trusted, each by the
control rather than by inspection. That is the pattern worth copying.

---

## Pre-registration

Sent as its own message, before anything ran.

**Claim, sharpened:** In CPython, calling `next(c)` on a single `itertools.count()` object
concurrently from N OS threads yields each integer exactly once — no value duplicated or
skipped — for the default integer counter.

**H₀:** Concurrent `next()` on one shared `itertools.count()` (default args) never returns a
duplicate value, regardless of thread count, switch interval, or magnitude of the counter — so
a single shared counter is safe for handing out unique IDs to worker threads.

**H₁:** Uniqueness is not a property of `count()` itself but of the GIL holding across its
C-level `next` for the integer fast path. Where that single-C-call property doesn't hold —
non-integer start values whose `__add__` is Python-level, or a free-threaded build —
duplicates appear. Thread-safety is therefore incidental and implementation-scoped, not a
guarantee of the type.

**Rejected if:** any run collects `total_calls != len(set(values))` — at least one duplicated
value — from a shared `count()`. **Also rejected if the positive control shows no duplicates**,
since that would mean the harness cannot detect races at all and no result from it is
trustworthy.

That second rejection clause is the load-bearing one. It is a falsification condition aimed at
the *experiment* rather than at the claim, and it is what turned three broken runs into
findings instead of into a `Verified`.

Note also what H₁ buys. "It's safe" versus "it's not safe" would have produced a test of
`count()` with default arguments, which is exactly the input where both hypotheses agree. H₁
names the *mechanism* — the increment completing inside one C call — and a mechanism tells you
which input separates the two: one where the increment has to run Python bytecode.

## Harness defect 1 — the control came back clean

First run, 8 threads × 20,000 `next()` calls:

```
control: pure-Python counter       calls=160000  unique=160000  duplicates=0       clean
itertools.count()                  calls=160000  unique=160000  duplicates=0       clean
itertools.count(2**63)             calls=160000  unique=160000  duplicates=0       clean
itertools.count(0.0, 1.0)          calls=160000  unique=160000  duplicates=0       clean
itertools.count(Decimal(0), 1)     calls=160000  unique=160000  duplicates=0       clean
```

Every row clean, including a pure-Python `v = self.n; self.n = v + 1` that is textbook racy.
By the pre-registered condition, the entire run is void — and note how *good* it looks. Five
clean rows over 160,000 contended calls is precisely the output a run would quote to justify
"thread-safe, verified."

Two defects behind it: threads were started in a loop with no barrier, so thread 0 likely
finished its 20,000 iterations before thread 7 started; and `setswitchinterval` was called
*after* the environment stamp was printed, so the stamp reported a switch interval the run
didn't use.

## Harness defect 2 — the control was blind, not merely unlucky

Rebuilt with a `threading.Barrier` and 10× the volume. The control was *still* clean at 1.6M
calls. Rather than accept that, the next step tested the harness itself:

```
overlap window: 74.75 ms (positive = all 8 threads were simultaneously inside their loop)
VeryRacy (sleep(0) in window)    calls=160000  unique=20677   dups=139323
Racy (plain += shape)            calls=1600000 unique=1600000 dups=0
```

This is the diagnosis that mattered. The threads genuinely overlap for 75 ms, and the harness
*can* see a race — 139,323 duplicates when the read-modify-write window contains an explicit
GIL drop. What it cannot see is the plain `+=` shape, which on this build is simply not
preempted inside its two-bytecode window. So the control was not a weak control; it was a
**blind** one, and a blind positive control is indistinguishable from a passing experiment.

The proven-sensitive counter replaced it.

## Harness defect 3 — a probe that never fired

The row meant to test H₁'s mechanism used `class SlowInt(int)` with a Python-level `__add__`,
on the assumption that `count()` would call it. Before reporting that row's clean result, the
run instrumented the assumption:

```
count(SlowInt(0), 1)  -> values [0, 1, 2, 3, 4]  __add__ calls: 0
                         value types: ['int', 'int', 'int', 'int', 'int']
```

`__add__` called **zero** times, values coming back as plain `int`. `count()`'s fast path takes
any `PyLong`, subclasses included, so the discriminating row had been discriminating nothing —
a clean result there was an artifact of the probe never running. (The same probe also turned up
`TypeError: a number is required`: `count()` rejects a non-numeric start outright, so the
replacement type needed `__float__` to get past the check.)

A dead probe is the concurrency version of `assert` never being reached. It is only visible if
you check that the mechanism you are testing actually engaged.

## Raw output — the run that counted

```
python      3.14.7 (main, Aug  5 2026, 10:29:49) [Clang 21.0.0 (clang-2100.1.1.101)]
platform    macOS-26.5.2-arm64-arm-64bit-Mach-O / arm64
impl        CPython 3.14.7
free-thread GIL disabled = False
harness     8 threads x 200000 next() = 1600000 calls, switchinterval=1e-06

control: racy counter (must RACE)  calls=160000  unique=20773   duplicates=139227  RACE
itertools.count()                  calls=1600000 unique=1600000 duplicates=0       clean
itertools.count(2**63)             calls=1600000 unique=1600000 duplicates=0       clean
itertools.count(0.0, 1.0)          calls=1600000 unique=1600000 duplicates=0       clean
itertools.count(Decimal(0), 1)     calls=1600000 unique=1600000 duplicates=0       clean
itertools.count(Num(0), Num(1))    calls=160000  unique=20360   duplicates=139640  RACE
```

The `Num` class is the whole experiment: a real non-`int` number that `count()` stores and
increments through `PyNumber_Add`, dispatching to a Python-level `__add__` that yields between
the read and the store.

```python
class Num:
    """count() stores it and calls PyNumber_Add per next(), which dispatches to this
    Python-level __add__ -- which yields. __float__ gets it past count()'s
    'a number is required' check."""
    def __init__(self, n): self.n = n
    def __add__(self, other):
        n = self.n
        time.sleep(0)  # GIL drop between count()'s read and its store
        return Num(n + other.n)
    def __float__(self): return float(self.n)
    def __hash__(self): return hash(self.n)
    def __eq__(self, o): return isinstance(o, Num) and self.n == o.n
```

The dead `SlowInt` probe was kept in the script with a docstring explaining why it is dead,
rather than deleted. A future reader reaching for an `int` subclass will find out here instead
of by getting a clean row.

## Verdict

**Refuted** — CPython 3.14.7, GIL-enabled, as H₀ was stated.

**H₀ was:** "Concurrent `next()` on one shared `itertools.count()` never returns a duplicate,
**regardless of thread count, switch interval, or magnitude of the counter**."

**Observed:** `count(Num(0), Num(1))` — 160,000 calls, 20,360 unique, **139,640 duplicates**.
`next()` is not atomic: it reads, adds, then stores, and the add can yield.

**Now believed:** H₁. Uniqueness comes from the increment completing inside one C call without
releasing the GIL — true for the integer fast path, and for `float` and `Decimal` whose
`__add__` is also C and doesn't yield; false the moment the add runs Python bytecode.

The strongest form of H₀ is what made this decidable. "Regardless of … magnitude of the
counter" is the clause that put every `count()` code path on trial, not just the one the user
had in mind. A hedged H₀ — "safe for typical use" — would have survived this output, and
survived it without teaching anyone anything.

The practical claim underneath (default `count()`, plain integers, GIL build) did survive 1.6M
contended calls. It survives by implementation accident rather than by contract, which is a
different thing to be told than "verified."

## What stayed untested, and why that is in the report

The free-threaded build. This interpreter has the GIL enabled (`GIL disabled = False`), so the
case where the fast path's protection is most likely to disappear could not be run at all —
and it is exactly where H₀ would be expected to fail for plain integers too. Naming the trial
that would settle it (`python3.14t`, same script) is the difference between a scoped verdict
and an overclaimed one.

## Consequences

Don't share a bare `count()` for ID generation: `next()` is not documented atomic, and the
property being relied on is CPython-and-fast-path-specific. A lock around a plain integer is a
guarantee rather than a coincidence, `uuid4()` avoids the shared counter entirely, and
`count(worker_id, num_workers)` per thread means there is nothing shared to race on.
