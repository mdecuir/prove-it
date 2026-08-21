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
- [Claims about systems you can't run](#claims-about-systems-you-cant-run)
- [Claims that aren't empirical](#claims-that-arent-empirical)

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

Execution demonstrates presence directly and absence only by argument. A failed probe shows *that probe* failed; on its own it cannot distinguish "the feature doesn't exist" from "it exists under a different name, on a different object, behind a flag, or in a submodule you didn't import."

But that is not the end of it, and treating every absence claim as unsettleable is its own failure. How much can be established depends on whether the surface is closed.

### First, decide the shape of the claim

Two questions, before designing anything.

**Is the surface closed or open?**

A **closed** surface can be enumerated and read to the end. A stdlib module, an installed pure-Python package, a vendored dependency — you can list every attribute, read every line that implements the relevant paths, and know you have seen all of it. Absence here is a claim about a finite object, and a finite object can be exhausted. **Verified is reachable**, scoped to the version.

An **open** surface cannot. Signs it is open: a service behind an API; `__getattr__` or `__getattribute__` synthesising attributes on demand; a plugin registry or entry points a third party can add to; dispatch through a C extension or binary you cannot read; anything configured by environment or remote state. Absence here is a claim about an unbounded space, and the honest verdict stays **Inconclusive, with strong negative evidence**.

Do not assume the answer. `dir()` on a module with a module-level `__getattr__` looks closed and is not.

**Is the claim about the library, or about what you can achieve with it?**

"`zipfile` does not store file ownership" and "you cannot preserve ownership through a zip" are different claims, and the second is usually what the user meant. A library that does not participate in a feature may still carry it: an opaque bytes field that round-trips intact lets you encode ownership yourself and apply it on extract, so the library is a courier rather than a participant. Settle whichever claim was made, and say plainly if the other one has a different answer.

### Then decompose absence into presence

This is the move that makes a closed-surface absence claim tractable, and it is worth reaching for before the convergent-evidence checklist below.

"There is no way to X" is one unfalsifiable claim. Split it along the paths X would have to travel, and each piece becomes a positive claim that a single run can reject:

- does the **write** path record it?
- does the **object model** expose it?
- does the **read** path apply it?

Each leg is now falsifiable by observation rather than by failure to find. If all three hold and the surface is closed, you have a conjunction of settled positives, not an argument from ignorance — which is why `Verified` is defensible there. If any leg cannot be closed, that leg is what makes the whole thing Inconclusive, and you can say exactly which.

Pair the negative legs with a control that proves the probe would have detected the feature had it been present. A run showing "extract produced uid 501, not the archive's 12345" means much more alongside "and a real `chown(12345)` in this harness raises" — without it, the negative is indistinguishable from a probe that never fired.

### Convergent evidence, for what the legs don't cover

1. Probe the obvious API surface and show it failing.
2. Enumerate the actual surface — `dir()`, `__all__`, `__slots__`, `inspect.signature`, the type stubs — and show the feature isn't in it.
3. Search the installed source, not just the public API. Grep the implementation of the specific paths, not the package as a whole.
4. Check the documentation and changelog for the feature under other names.

**Coincidental matches are the specific hazard here.** Searching bytes or source for something you expect to be absent produces false positives, and a false positive on an absence claim reads as a refutation. A run searching a zip archive for a gid of `20` found two matches, both of which were the `version_needed` field holding `\x14\x00` for "2.0". Disambiguate every hit by offset or context before letting it change the verdict — an unexamined match is as bad as an unexamined `AttributeError`.

### Verdicts

- **Closed surface, all legs settled, control in place** → `Verified`, scoped to the version and to the exact claim (library-does-not vs cannot-be-achieved).
- **Closed surface, a leg you couldn't settle** → `Inconclusive`, naming the leg.
- **Open surface** → `Inconclusive, with strong negative evidence`, listing what was searched. This phrasing beats false certainty because it tells the user which further search might still pay off.

**False green:** one `AttributeError` reported as proof the feature doesn't exist. **And its mirror image:** an open surface treated as closed, so a `Verified` gets issued over a space that was never exhaustible — same error, opposite direction, and harder to spot because the report looks thorough.

---

## Concurrency and ordering claims

*"This is thread-safe." "Results come back in submission order."*

A passing run proves the bad interleaving didn't happen this time, not that it can't. Never report a single clean run as verification of a safety property. H₀ ("this is thread-safe") and H₁ ("it is unsafe on an interleaving this run didn't hit") predict the same clean output, which is why no number of green runs discriminates and why the honest verdict here is usually Inconclusive.

What helps: run many iterations, add contention (more workers than cores), insert delays at the suspected interleaving point to widen the window, and use the available deterministic tooling — thread sanitizers, `pytest-repeat`, race-detection modes — rather than repetition alone.

For ordering claims, distinguish *guaranteed* order from *observed* order. Many APIs return submission order in practice under light load and stop doing so under contention. Test under contention, or scope the verdict to "observed, not guaranteed."

The realistic verdict for a thread-safety claim is usually **Inconclusive** with a note that only the documentation or the source can establish the guarantee. Say that rather than manufacturing confidence from a hundred green runs.

**False green:** one clean concurrent run, reported as "thread-safe, verified."

---

## Claims about systems you can't run

*"The managed bulk-import path costs less than streaming the same rows in." "That warehouse query will finish inside the batch window at production volume."*

The claim is empirical. Somebody could settle it. It just isn't going to be settled from here, because settling it means real money, production access, or terabytes you don't have. The verdict is **Untested**, and the work is decomposition rather than execution.

Split the claim along the boundary of what you can reach:

1. **Run the local half.** There nearly always is one, and it is nearly always where the surprises are. A claim about an import endpoint's throughput sits downstream of a payload you generate yourself: how long does generating it take, how large is it really, is the on-disk format the one you assumed, does the row count match. The `examples/reread-cost.md` case in this repo started as exactly this — the untestable cloud half was set aside and the local file-reading half turned out to decide the design question on its own.
2. **Source the remote half, and mark it as sourced.** Published pricing, documented quotas, service limits, the changelog. Cite it with a date. Vendor-stated numbers are evidence of a different kind from observed ones, and the report must not blur them — "the docs say 100 MB/s" and "we measured 100 MB/s" fail in different ways, and only the second one is yours.
3. **Name the smallest real trial that would settle it.** Not "test it in production" but the specific minimal thing: one import of N rows into a scratch instance, with the two figures to record. This is the part someone with the access can actually act on, and it is what makes an Untested verdict useful rather than merely honest.

**On scaled-down proxies.** Run one when it exists, and say what does not extrapolate. Three things routinely don't: anything with volume pricing tiers, anything with a cold-start or cache-warming component, and anything under contention. A proxy at 1/1000 scale answers a question about 1/1000 scale, and the interesting claims are usually about the part that only appears at full size.

**Never lift the barrier by provisioning.** Do not create the cluster, the bucket, or the instance to settle a claim, even when the API call is one line and the free tier would probably cover it. The cost of being wrong is an invoice or an incident, and it is not your call to make. Ask.

**False green:** the vendor's documentation agrees with the claim, so it is reported as **Verified**. Nothing was observed; a citation was found. That is a documentation lookup, and calling it verification is precisely the confusion this skill exists to prevent.

---

## Claims that aren't empirical

*"This API is well designed." "polars is more readable than pandas." "You should use a queue here."*

No observation settles these, and the tell is that no result would change anyone's mind. Reach for the falsification condition and nothing comes: there is no output that the claim's proponent would accept as refuting it.

The failure mode is not usually refusing to test them. It is **testing an adjacent claim and presenting it as the answer.** "Is this API well designed" quietly becomes "does this API require fewer lines for the common case," which is measurable, and gets measured, and the measurement is then offered as though it settled the original. It didn't. It settled a proxy that happens to be executable, chosen because it was executable.

So: say the claim isn't empirical, say what is ambiguous in it, and then **answer the underlying question directly** — with judgement, experience, and reasoning, which is what it wanted in the first place. Sometimes a measurable sub-claim genuinely is worth settling on the way; run it if so, but present it as one input into a judgement rather than as a verdict on the whole.

One thing worth checking before routing a claim here: whether it *contains* a testable claim it is being confused with. "Library A is nicer to use than B" is a preference, but "A needs no adapter for this input while B does" is a fact, and it may be the thing actually in dispute. Sharpening in step 1 is where that gets separated out, and finding a real testable claim underneath is a better outcome than an Ill-posed verdict.

**False green:** a measurable proxy is substituted for an unmeasurable claim, and the proxy's clean result is reported as having settled it.
