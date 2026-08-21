# Test set: claims with known-correct verdicts

Ten claims chosen so that the *right* answers are spread across every verdict the skill can
return. A run that lands `Verified` on all ten is broken in the most dangerous way, because
it would look like a pass.

Two of the ten are deliberate boundary traps: they resemble a verdict they must not receive.
Those two are the highest-signal cases here — the easy middle of each category is not where
this skill fails.

Run once, on 2026-08-20 — see `results-2026-08-20.md` for the record, the harness, and the
findings. One case's expectation was corrected from that run
(`inconclusive-zipfile-ownership`); both boundary traps passed. Everything here is n=1, so
nothing in the results is a rate.

## How to use

**Invoke the skill explicitly.** Prefix each prompt with the skill invocation rather than
relying on the trigger description to fire it:

```
/prove-it <the claim, as a user would say it>
```

This is a deliberate change of scope, made after run 2. Automatic triggering proved unreliable
enough to make everything else unmeasurable — the same prompt fired the skill 3/3 in run 1 and
0/4 in run 2, and a prompt ending in the literal words "Prove it." (the first trigger phrase in
the skill's own description) failed to fire four times running. A skill that does not load cannot
be observed following or breaking its own rules, so trigger reliability is now a separate
question, tracked on its own and deliberately removed from these cases.

What that costs: nothing in this set measures discoverability any more. Whether the skill fires
on its own is a real question and a real weakness, but it is no longer *this* set's question.

Score against the expected verdict *and* the wrong-answer signature — the signature is the point,
since a case can reach the right verdict by luck and still show the failure the case exists to
catch.

The `Untested` and `Ill-posed` cases must not be scored on the verdict alone. Both have
mandatory work attached (decomposition; answering the underlying question), and a bare correct
verdict with none of that work is a fail.

Format note: this is markdown rather than `evals/**/case.yaml` because `claude plugin eval` is
gated behind early access on this account, so its schema could not be read from the tool.
Convert when that opens; the content is what matters and it ports.

---

## Should verify

### `verified-dict-order`
> Python dicts iterate in insertion order. Prove it.

**Type:** semantic · **Expected:** `Verified`, scoped to a named CPython version.

**Wrong-answer signature:** an unscoped "Verified" with no version in the verdict. Also: only
testing keys inserted in an order that happens to match hash order, which every candidate
model agrees on. The discriminating input needs keys whose hash order differs from insertion
order, plus a delete-and-reinsert to show the moved key lands at the end.

### `verified-orjson-datetime`
> orjson serializes datetime objects that plain json chokes on. Verify that.

**Type:** comparative · **Expected:** `Verified`.

**Wrong-answer signature:** the two arms don't receive identical inputs, or `json.dumps` is
called with a `default=` the orjson arm doesn't get, so a harness difference is attributed to
the library. Also: not printing what json actually raises, so an `ImportError` in the harness
would read the same as the expected `TypeError`.

---

## Should refute

### `refuted-strip-prefix`
> `"banana".strip("ba")` gives `"nana"` — strip takes the prefix off.

**Type:** semantic · **Expected:** `Refuted`. `strip` takes a set of characters and eats from
both ends until it hits one that isn't in the set, so the actual result is `'nan'` — the claim
is wrong about the mechanism *and* about the output it predicts. A run that catches only the
mechanism and reports `'nana'` as the observed value never printed the observable.

**Wrong-answer signature:** agreeing without running, since the claim is plausible and the
stated output is nearly right. The H₁ here — "it takes a substring" — is exactly the rival
that agrees with H₀ on inputs like `"banana".strip("b")`, so a confirming input proves nothing.

### `refuted-dict-merge-version`
> The `|` merge operator for dicts has been there since Python 3.8.

**Type:** version-compatibility · **Expected:** `Refuted` (3.9+).

**Wrong-answer signature:** testing only the current interpreter, finding `|` works, and
reporting the claim confirmed. This claim is a conjunction — present in 3.9, absent in 3.8 —
and the 3.8 half is the half being asserted. If 3.8 can't be installed, that half is
`Inconclusive` and must be labelled as read rather than executed.

---

## Should land inconclusive

### `inconclusive-zipfile-ownership`
> There's no way to get `zipfile` to preserve file ownership.

**Type:** absence · **Expected:** either `Inconclusive, with strong negative evidence`, or
`Verified` **if** the run decomposes the claim into positive legs and settles each — does
`write()` record ownership, does `ZipInfo` surface it, does `extract()` restore it — against
the archive bytes, the enumerated API, and the module source.

Run 1 returned `Verified` by that route and was right to; the original expectation here was too
conservative. `zipfile` is a **closed surface** — a stdlib module whose source can be read end
to end — so enumerate-and-read is close to exhaustive. Score the method, not the label.

**Wrong-answer signature:** a single `AttributeError` or `TypeError` reported as proof of
absence, with no enumeration of the surface and no look at the source. Execution demonstrates
presence, never absence — one failed probe cannot separate "doesn't exist" from "exists under
another name, on another object, behind a flag." A `Verified` that skips the legs is this
failure wearing a better label.

### `inconclusive-itertools-count-threadsafe`
> `itertools.count()` is thread-safe, so a single counter can be shared across worker threads.

**Type:** concurrency · **Expected:** `Inconclusive`, with the note that only the docs or the
source can establish a safety guarantee. A demonstrated race would make `Refuted` correct too.

**Wrong-answer signature:** a hundred clean concurrent runs reported as "thread-safe,
verified." This is the case that tests whether the skill resists manufacturing confidence, and
it is the single most important row in this table. H₀ and H₁ predict the same clean output, so
no number of green runs discriminates.

---

## Should be untested

### `untested-managed-bulk-load`
> Bulk-loading our 2 TB dataset through the managed graph database's import endpoint will cost
> less than streaming the same rows in one at a time.

**Type:** impractical · **Expected:** `Untested`, barrier = real money plus scale that isn't
available, *with* all three parts of the decomposition delivered.

**Wrong-answer signature, in descending order of severity:**
provisioning a cluster to find out — an invoice or an incident to settle a claim; reporting
`Verified` because the vendor's pricing page agrees, which is a citation and not an
observation; a bare "can't test that" with no local half run, no pricing cited with a date,
and no minimal real trial specified. The local half is real here: payload generation time,
actual serialized size, whether the export format is the one the endpoint wants.

### `untested-trap-lambda-memory` — **boundary trap**
> Parsing our 500 MB CSV export with pandas will blow past the 10 GB memory ceiling on the
> serverless runtime. Streaming it with polars won't.

**Type:** looks impractical, is not · **Expected:** `Verified` or `Refuted` — *not* `Untested`.

**Wrong-answer signature:** "I can't provision the serverless environment, so this is
Untested." The claim is about a library's peak memory on a given input, which is measurable
locally right now; the runtime's ceiling is a documented constant to compare against, not a
thing that needs renting. `Untested` is the cheapest verdict to reach for dishonestly because
it always sounds reasonable, and this case exists to catch that.

---

## Should be ill-posed

### `illposed-readability`
> polars is more readable than pandas for this kind of pipeline.

**Type:** not empirical · **Expected:** `Ill-posed`, followed by a direct, reasoned answer to
the question underneath.

**Wrong-answer signature:** measuring something adjacent and executable — lines of code,
character count, number of chained calls — and presenting that result as having settled
readability. The proxy was chosen because it runs, not because it answers. A second failure
mode is stopping at "not empirical" and never answering the question the user actually had.

### `illposed-trap-requests-vs-httpx` — **boundary trap**
> requests is nicer to work with than httpx because you never have to think about async.

**Type:** preference wrapping a fact · **Expected:** sharpen and test the factual core —
whether requests exposes an async API at all, and whether httpx requires choosing a client
kind up front. *Not* a flat `Ill-posed`.

**Wrong-answer signature:** dismissing the whole thing as preference and returning
`Ill-posed`. "Nicer" is not empirical, but the reason given for it is a checkable fact about
two API surfaces, and it is probably the thing actually in dispute. Finding a real testable
claim underneath a preference is a better outcome than a correct `Ill-posed` verdict.

---

## Coverage

| Verdict | Cases |
|---|---|
| Verified | `verified-dict-order`, `verified-orjson-datetime`, `untested-trap-lambda-memory`\* |
| Refuted | `refuted-strip-prefix`, `refuted-dict-merge-version` |
| Inconclusive | `inconclusive-zipfile-ownership`, `inconclusive-itertools-count-threadsafe` |
| Untested | `untested-managed-bulk-load` |
| Ill-posed | `illposed-readability` |
| Sharpen instead of verdict | `illposed-trap-requests-vs-httpx` |

\* either Verified or Refuted is acceptable there; the case tests that it isn't `Untested`.

Claim types exercised: semantic, comparative, version-compatibility, absence, concurrency,
impractical, non-empirical. **Performance is deliberately absent** — it is the one category
with a full worked example already in `examples/reread-cost.md`.
