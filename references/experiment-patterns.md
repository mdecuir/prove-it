# Experiment patterns by claim type

Read the section matching the claim. Each gives the shape of a discriminating experiment and the specific way that claim type tends to produce a false green.

Each section also names the rival hypothesis (H₁) that claim type is usually confused with. That rival is the design input: an experiment that cannot tell H₀ from its most plausible neighbour has not tested anything, however green it comes back.

- [Semantic claims](#semantic-claims)
- [Comparative claims](#comparative-claims)
- [Performance claims](#performance-claims)
- [Exception claims](#exception-claims)
- [Version and compatibility claims](#version-and-compatibility-claims)
- [Absence claims](#absence-claims)
- [Concurrency and ordering claims](#concurrency-and-ordering-claims)

---

## Semantic claims

*"`dict.pop()` returns the value, not the dict." "`str.split()` with no argument collapses runs of whitespace."*

The simplest case. Call the real function, print the observed result, compare to the prediction.

The design work is in input selection. One input where the claim obviously holds proves almost nothing — a wrong model of a function usually agrees with the right one on typical inputs and diverges at the edges. Choose the inputs that separate H₀ from H₁: empty, single-element, duplicate, boundary value, wrong type, unicode past the BMP, whatever the claim's specific failure mode would be.

H₁ for a semantic claim is usually a *different mechanism producing the same output on easy inputs* — a substring where you claimed a character set, a view where you claimed a copy, a coercion where you claimed a passthrough. Write it down first; it tells you which input to pick.

Print the type as well as the value. A surprising number of behavior claims are really claims about type, and `5` and `5.0` and `Decimal("5")` print similarly enough to slip past.

**False green:** testing three inputs that are all the same case in different clothes.

---

## Comparative claims

*"`orjson` handles datetimes that `json` chokes on." "requests follows redirects by default but httpx doesn't."*

Same harness, same inputs, only the library varies. Write one function that takes the option as a parameter, then call it twice — this makes it structurally impossible for the two arms to drift apart in ways you didn't intend.

Print both results side by side, including the case where they agree. Agreement is a finding: H₁ for every comparative claim is "the two behave the same here," and a claim that two libraries differ is rejected by them behaving identically. That outcome needs to be as visible as the confirming one.

Install both into the same throwaway environment and print both versions.

**False green:** the two arms receive subtly different inputs, or one is called with a default the other doesn't have, and the resulting difference is attributed to the library rather than the harness.

---

## Performance claims

*"`orjson.dumps` is faster than `json.dumps`." "This regex is the bottleneck."*

The most failure-prone category, because a number always appears and numbers look like evidence.

This is the one place where H₁ is the statistical null: **H₀ is "A is faster than B by margin M on workload W" and H₁ is "the difference is inside run-to-run variance."** State M before running. Without a margin committed up front, any nonzero difference reads as support, which is how the failure below happens.

Requirements:

- **Warmup.** Discard the first runs. JIT, import cost, page faults, and cache state all land on run one.
- **Repetitions and variance.** Report median and spread, never a single figure. Use `timeit`, `hyperfine`, `benchmark.js` — a purpose-built harness rather than a hand-rolled `time.time()` delta.
- **A realistic workload.** A microbenchmark on a 3-element list answers a question nobody asked. Size the input to the actual use case, and say what size was used.
- **Magnitude, not just direction.** "A is faster" is not actionable. "A is 1.04× faster, well inside run-to-run variance" and "A is 40× faster" are different findings, and the first should be reported as *no meaningful difference* rather than a win.
- **Check what's actually being measured.** If both arms spend 95% of their time in I/O or in shared setup, the benchmark is measuring that, and the difference under test is invisible regardless of what the totals say.

State the machine. Performance results are not portable and a result without hardware context will be over-generalized by whoever reads it next.

**False green:** a 3% difference from one run of each, reported as a decisive win.

---

## Exception claims

*"It raises `ValueError` on malformed input." "That call fails silently rather than throwing."*

Assert on the exception *type*, and print the full message and traceback. Catching bare `Exception` and declaring the claim confirmed is the standard failure here — the code may well be raising, just for an entirely different reason than the claim states, often an `ImportError` or `TypeError` from the harness itself.

Always run the near-miss: the input that should *not* raise. A script where everything raises confirms nothing about the trigger condition.

For "fails silently" claims, prove the absence of the exception *and* show what the call returned instead. Silence has a value attached to it, and that value is usually the interesting part.

**False green:** `except Exception: print("raises as claimed")`, hiding a typo in the harness.

---

## Version and compatibility claims

*"This was added in 3.11." "The v2 API removed that parameter."*

Test at the boundary, on both sides. A claim that something appeared in version N is a conjunction of two claims — present in N, absent in N-1 — and only testing N verifies half of it. H₁ is "it was already there in N-1," which is precisely the half a confirming test skips.

Use pinned installs into separate throwaway environments, one per version. Print the resolved version from inside the running process (`lib.__version__`, `importlib.metadata.version`), not from the install command's output. What the resolver actually installed and what you asked for diverge more often than expected, and this is where silent version drift enters.

If the older version can't be installed in the current environment — dropped Python support, unavailable wheels — that's an inconclusive result on that half, and the documentation changelog is the fallback. Say which half was executed and which half was read.

**False green:** verifying the feature exists in the new version, assuming the absence in the old one.

---

## Absence claims

*"The library doesn't support X." "There's no way to configure that."*

Structurally the hardest, and worth being explicit with the user about why: execution can demonstrate presence but not absence. A failed probe shows *that probe* failed. It cannot distinguish "the feature doesn't exist" from "it exists under a different name, on a different object, behind a flag, or in a submodule you didn't import."

H₁ is not "the feature exists" but the specific ways it could exist unseen: under another name, on another object, behind a flag, in an unimported submodule. Enumerate those before probing — they are the search plan.

The best available approach is convergent evidence:

1. Probe the obvious API surface and show it failing.
2. Enumerate the actual surface — `dir()`, `inspect.signature`, the type stubs, the module's `__all__` — and show the feature isn't in it.
3. Search the installed source, not just the public API.
4. Check the documentation and changelog for the feature under other names.

Then report it as *no evidence found across these four probes*, not as proof of absence. The honest verdict for most absence claims is **Inconclusive, with strong negative evidence** — and that phrasing is more useful to the user than false certainty, because it tells them what kind of further search might still pay off.

**False green:** one `AttributeError` reported as proof the feature doesn't exist.

---

## Concurrency and ordering claims

*"This is thread-safe." "Results come back in submission order."*

A passing run proves the bad interleaving didn't happen this time, not that it can't. Never report a single clean run as verification of a safety property. H₀ ("this is thread-safe") and H₁ ("it is unsafe on an interleaving this run didn't hit") predict the same clean output, which is why no number of green runs discriminates and why the honest verdict here is usually Inconclusive.

What helps: run many iterations, add contention (more workers than cores), insert delays at the suspected interleaving point to widen the window, and use the available deterministic tooling — thread sanitizers, `pytest-repeat`, race-detection modes — rather than repetition alone.

For ordering claims, distinguish *guaranteed* order from *observed* order. Many APIs return submission order in practice under light load and stop doing so under contention. Test under contention, or scope the verdict to "observed, not guaranteed."

The realistic verdict for a thread-safety claim is usually **Inconclusive** with a note that only the documentation or the source can establish the guarantee. Say that rather than manufacturing confidence from a hundred green runs.

**False green:** one clean concurrent run, reported as "thread-safe, verified."
