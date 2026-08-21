---
name: prove-it
description: >-
  Settle a claim about how code or a system actually behaves, instead of asserting it again. First
  classify the claim, then act: testable here (design and run a minimal experiment against the real
  library, and report the result even when it refutes the claim), empirical but out of reach because
  of cost, scale, production access, or credentials (verdict Untested — run whatever local half
  exists, cite the rest as sourced, never provision billable infrastructure), or not empirical at all
  (verdict Ill-posed — say so, then answer the real question). Use when someone says "prove it", "are
  you sure?", "verify that", "show me", "how do you know", "test that", or disputes an assertion about
  what a function returns or raises, what a default is, how two libraries compare, what a version
  changed, whether something is thread-safe, how fast or how memory-hungry something is, or what an
  infrastructure or cloud operation will cost. Also use proactively, before building on any unverified
  assumption about library behavior, version compatibility, performance, capacity, or cost — including
  assumptions you stated yourself a moment ago.
---

# Prove It

An assertion about library behavior is a report from memory. Memories of API surfaces go stale, blur across adjacent versions, and confabulate details that are plausible rather than true — and they do it most confidently for libraries that are well known, because familiarity is what generates the confidence, not recall accuracy.

This skill replaces the assertion with an experiment. The claim gets restated as something that could be false, an experiment gets designed that could show it false, the code runs against the real library, and the raw output decides.

The load-bearing property is that **the experiment must be able to refute the claim**. An agent testing its own assertion has an obvious pull toward writing the test that passes. Everything below is structured to make that harder.

## Triage first

Three questions, in order. They lead to different work, and misrouting here wastes more effort than any later mistake.

**1. Could any observation settle this?** If no, the claim is not empirical. Design and style preferences, what the documentation *recommends*, roadmap speculation, "is this idiomatic" — no run decides these, and a run that appears to is measuring something else. Verdict **Ill-posed**. Say what would have to be pinned down to make it a claim, and answer the underlying question directly instead. There is usually a real question behind it that deserves a real answer.

**2. Can the experiment be run from here, at acceptable cost?** If no, the claim is empirical and the experiment is real, but it is out of reach. Verdict **Untested**, and see below — this is a distinct outcome with actual work attached, not a shrug.

**3. Otherwise, run the procedure.** Settle by execution: return values, raised exceptions, default arguments, ordering and stability guarantees, mutation vs. copy semantics, encoding and coercion behavior, version compatibility, and relative performance between two concrete options.

A fabricated experiment is far worse than an honest "I can't settle that from here." So is a real experiment that quietly answers an easier question than the one asked.

### When the experiment is impractical

An **Untested** verdict has to name its barrier. Only these count:

- **Real money.** Provisioning managed infrastructure, egress, per-request billing at meaningful volume.
- **Irreversible or outward-facing side effects.** Writes to production, sends to third parties, anything with a blast radius.
- **Scale that isn't available.** The claim is about terabytes, thousands of concurrent clients, or months of accumulated data, and it does not hold at toy scale.
- **Wall-clock beyond the session.** Hours-long jobs, multi-day soak tests.
- **Access you don't have.** Credentials, a licensed dependency, specific hardware, a private network.
- **An external dependency you don't control.** A third-party service whose behavior can change under you, making any result unreproducible.

Never remove one of these barriers by provisioning billable or irreversible resources to settle a claim. The claim is not worth the invoice or the incident, and this skill's habit of "just run it" is exactly the wrong instinct here. Ask, don't proceed.

Naming a barrier is necessary but not sufficient, because **Untested** is the easiest verdict to reach for dishonestly — it costs nothing and it always sounds reasonable. Earn it by decomposing the claim into three parts and reporting each:

- **What is testable here.** Almost always more than zero. A claim about a managed service's bulk-import throughput still has a local half: how long generating the input takes, what the payload size actually is, whether the file format is what you assumed. Run that half.
- **What has to be sourced instead.** Published pricing, documented limits, service quotas, a changelog — with a citation and a date, because these change. Cite what the vendor states, and mark it as vendor-stated rather than observed.
- **What nobody can settle without the real thing,** and what specifically would settle it — the smallest real-world trial that would decide it, so someone with the access can act on it.

A scaled-down proxy is worth running when it exists, but say plainly what does not extrapolate from it. Costs with volume tiers, anything with a cold-start or warm-cache component, and anything contended are the usual places where small-scale results mislead about large-scale behavior.

The pattern for this claim type is in `references/experiment-patterns.md`.

## Procedure

### 1. Restate the claim as a falsifiable proposition

The original assertion is usually too loose to test. Sharpen it, and show the sharpened version — the user needs to see what is actually about to be tested, because the gap between what was said and what gets tested is where bad verifications hide.

A testable proposition names: the exact call or operation, the exact input, the expected observable, and the environment it's claimed to hold in. "`sorted()` is stable" becomes "`sorted()` in CPython 3.12 preserves the relative order of elements comparing equal under the supplied key."

Behavior claims are always claims about a *(library, version)* pair. If the version is unstated, either pin the one the user's project actually uses or test across the plausible range and say which is which.

If sharpening changes the meaning of the claim, flag it and ask. Quietly testing a weaker proposition than the one asserted is a way of appearing to verify while verifying nothing.

### 2. State the null hypothesis, its rival, and the falsification condition — before anything runs

Send these three **as their own message**, before the first execution:

- **H₀ (null hypothesis):** the claim, in the strongest form it will bear. This is the proposition the experiment exists to prove false.
- **H₁ (rival):** the most plausible thing that is true instead, if H₀ falls.
- **Falsification condition:** the specific observable that would reject H₀.

That is two requirements, and the second is the one that quietly disappears.

**Before anything runs.** Not "before writing any code" — drafting the script and then pre-registering before you execute it is fine, because nothing has been observed yet. What must never happen is a prediction composed with output already in view. A prediction recorded after seeing output can be retrofitted to whatever appeared; one recorded before it cannot, and that difference is what converts "the test passed" into a statement with content.

**As its own message.** A Hypotheses *section* inside the final report is not evidence of pre-registration. It is an assertion about when something was written, and it cannot be checked — which is exactly the kind of thing this skill refuses to accept anywhere else. Only its position in the transcript, ahead of the first run, makes the ordering observable. A skill built on "don't tell me, show me" cannot make its own central guarantee unfalsifiable.

This failure is observed, not hypothesised. Run against its own test set, three of nine runs reasoned silently, executed, and emitted a single closing message containing the whole report — H₀, prediction, raw output, verdict — correctly ordered on the page and composed in the wrong order. The documents looked exemplary. Nothing in the finished artifact could have revealed it; only the transcript could. See `evals/results-2026-08-20.md`, finding 1.

H₀ here is the claim itself, not the statistical "no effect" default. The inversion is deliberate and load-bearing: an experiment that sets out to reject its own assertion is working against the agent's bias, whereas one that sets out to reject a boring null is working with it. Keep the claim on trial. (For performance and comparative claims the claim *is* the effect, so H₀ is "A is faster than B by margin M" and H₁ is "the difference sits inside run-to-run variance." Same rule, and it is what gives the variance requirement in `references/experiment-patterns.md` its teeth.)

Naming H₁ is what makes an experiment *discriminating* rather than merely confirming. A wrong model of a function usually agrees with the right one on ordinary inputs and diverges only at the edges, so the input worth running is the one that separates H₀ from H₁ — not the one that shows H₀ working. "`str.strip()` takes a set of characters" has the rival "it takes a substring," and the two agree on nearly every input a confirming test would reach for.

Stating H₀ in its strongest form is the anti-retrofit device. A hedged null survives anything, and if a refuting result later prompts a narrower claim, the narrowing is visibly a *different* H₀ rather than the same one clarified.

If no observable can be named that would reject H₀, stop. The claim is either vacuous, or not empirical, or not yet sharpened. Return to step 1 or say so plainly.

**Its own message, not its own turn.** Send the pre-registration and then keep going — the first execution follows immediately, in the same turn. Do not close on the pre-registration and wait, and do not ask whether to proceed. A text message with no tool call after it *ends the turn*, which hands the experiment back to the user as a question they did not ask. Three of twelve runs in run 4 did exactly that: a well-formed H₀/H₁/falsification message, correct in every respect, and then nothing ran. The pre-registration is a commitment made in passing, not a checkpoint. Ending the message with "Now running." and the first tool call in the same turn is the shape that works.

### 3. Design the minimal discriminating experiment

- **Exercise the real library.** Import and call the actual thing. A reimplementation, a mock, or a stub tests your model of the library, which is exactly the thing under suspicion. This is the single most common way an experiment ends up proving nothing.
- **Vary one thing.** For comparison claims, both options run through the same harness on the same inputs, with only the option under comparison differing.
- **Probe the boundary the claim depends on.** A claim about behavior at a threshold is tested at the threshold, on both sides. A claim that holds only in the easy case is not the claim that was made.
- **Include the near-miss case.** If the claim is "X raises on empty input," also run the non-empty input. Without it, a script that raises for an unrelated reason looks like confirmation.
- **Keep it small.** A twenty-line script that the user can read in one pass and re-run themselves is worth more than a thorough harness they have to trust.

Per-claim-type recipes are in `references/experiment-patterns.md`: semantic, comparative, performance, exception, version-compatibility, absence, and concurrency claims, plus the two that don't get run — claims about systems you can't reach, and claims that aren't empirical. Read it when the claim type isn't a straightforward "what does this return."

### 4. Write the script as a standalone, re-runnable artifact

Save it to a file rather than piping it through a shell heredoc. The script *is* the evidence, and evidence that can't be inspected and re-run is just a different flavor of assertion.

Every script prints its own environment first — language version, version of each library under test, platform. A result without its environment stamp is unfalsifiable later, when someone tries to reproduce it on a different machine.

Print observed values. Never let a bare `assert` stand as the result: `assert x == 5` passing tells the reader nothing about what `x` was, and a passing assertion is indistinguishable from an assertion that was never reached. Print the actual observable, then compare.

Install pinned versions into a throwaway environment (`venv`, `npx --yes`, a scratch directory). Do not mutate the user's project environment to run a verification.

### 5. Run it, and show raw output before interpreting it

Paste the actual output. Then interpret. Reversing this order lets the interpretation shape what gets shown, and readers lose the ability to check your reading against the evidence.

If the script errors, that is a result, not a setback to be quietly fixed. Distinguish "the experiment was broken" from "the claim is false" — they look similar from inside and mean opposite things. Fix genuine harness bugs; do not fix a harness until it produces the answer you expected.

### 6. Deliver a verdict

Restate H₀ verbatim in the verdict, beside the observation that decided it.

By the time a verdict gets written, H₀ is far up the transcript with script-writing and tool
output in between. A bare "Refuted" makes the reader scroll back to find out *what* was
refuted, and an agent writing the verdict is working from the same distance. Restating closes
that gap. Quoting the committed wording rather than paraphrasing from memory is also what
makes a retrofit visible — a paraphrase written after seeing the result is precisely where a
claim quietly narrows to fit.

Then say which hypothesis is now the operative belief, because rejecting H₀ does not install
H₁: H₁ was a conjecture too. If the observed behavior matches neither, flag that loudly. It
means the space of candidate models was drawn wrongly, not just that the wrong one was picked
out of it — and that is a much more useful thing for the reader to learn than a rejected H₀.

- **Verified** — H₀ survived a real attempt to reject it, under the stated environment. Strictly this is *failed to reject*, and that distinction is what forces honest scoping: "Verified for CPython 3.12" is defensible; bare "Verified" is almost always broader than the evidence.
- **Refuted** — H₀ was rejected. Say so directly and early, especially when the claim being refuted is one you made yourself earlier in the conversation. Name the correction: not just "that was wrong" but what the behavior actually is. This is the case that produces most of the value; treat it as the successful outcome it is, without hedging or burying it under context.
- **Inconclusive** — a real verdict, not a failure. The experiment ran but does not separate H₀ from H₁. State exactly what would.
- **Untested** — the experiment is real but out of reach. Name the barrier, report the part that *was* testable, cite what the rest rests on, and state the smallest real trial that would settle it. Never dress this up as Verified because the vendor's documentation agrees with the claim; documentation is a citation, not an observation.
- **Ill-posed** — no observation could settle the claim. Explain what's ambiguous, then answer the real question behind it.

### 7. Follow through to the source

A refuted claim usually has descendants. Find them:

- Code already written on the assumption — fix it or flag it.
- A plan or design decision that rested on it — reopen it.
- A doc, comment, or memory file that records it — correct it there, or the same wrong claim returns next session.

## Failure modes

Two tables, split by whether anyone has actually watched the failure happen. The distinction is
not decoration: the first table is evidence and the second is conjecture, and conflating them is
the same error the skill exists to prevent, committed in its own documentation.

Both are worth checking against before reporting. Only the first is worth trusting.

### Observed

Seen in real runs of this skill against `evals/test-claims.md`. The case column names where.

| Failure | What it looks like | Seen in |
|---|---|---|
| Whole report in one closing message | The model reasons silently, runs the experiment, then emits Claim, Hypotheses, Raw output and Verdict together. On the page the order is perfect; H₀ was composed with the output already in view. **Nothing in the finished artifact can reveal this** — only message order can, which is why step 2 requires its own message | `verified-dict-order`, `refuted-dict-merge-version` (run 1) |
| Uncited vendor facts, because triage never ran | Billing models, quotas and limits for named services stated confidently from memory, with no citation and no date. The claim was never classified, so the skill's own rule about sourcing the remote half never applied | `untested-managed-bulk-load`, both arms (run 1) |
| The skill never loads | Cost, capacity and preference claims do not trigger it, and triggering is unreliable even for prompts containing its own verbatim trigger phrases. A procedure that is not loaded cannot be observed following or breaking its rules | run 1 findings 2–3; run 2 (3/3 → 0/4) |
| The instrument was wrong, not the result | A verification whose *measurement* is broken while its subject is fine. Three in this skill's own evaluation: a regex that scored formatting instead of substance and reported failures that had not happened; an unpinned `--model` that left two runs non-comparable; a detector keyed on a tool call that slash invocation never emits | `evals/results-2026-08-21.md` |
| Version drift | Claim was about v2; the environment silently resolved v3. Observed in this skill's own harness rather than in a run — two runs were compared before anyone checked they used the same model | run 2 harness |
| Pre-registration ends the turn | H₀, H₁ and the falsification condition are sent correctly as their own message — and nothing runs, because a text message with no tool call after it *is* the end of a turn. The commitment gets made and the experiment gets handed back as a question nobody asked. Three of twelve runs, one of them closing with the words "Running now." | `verified-orjson-datetime`, `inconclusive-zipfile-ownership`, `inconclusive-open-surface-http2` (run 4) |
| Raw output paraphrased instead of printed | The verdict says "Observed: all four types raised `TypeError`" and the script's actual printed lines never appear. A `Verified` whose evidence is a summary of the evidence, in the run that otherwise followed the procedure most cleanly | `verified-orjson-datetime` (run 4) |
| Hallucinated follow-up turn | The report explains that H₀ has no truth value until a vendor and tier are named, then appends a fabricated user message supplying them: `user Neptune, provisioned db.r5.12xlarge, us-east-1. Now settle it.` It did not act on it. One step further along, the missing input gets invented and the claim gets "settled" against it | `untested-managed-bulk-load` (run 4) |

### Predicted, not yet observed

Reasoned about rather than witnessed. None occurred in the twenty-four runs that both engaged the
skill and executed something — the only population in which they *could* have been observed, out
of thirty-seven runs total. That is too small a sample to delete them, and large enough that they
should stop being presented as peers of the rows above.

Several are actively contradicted by what runs did instead. Controls appeared unprompted and
were used well: one run noticed its positive control came back *clean*, concluded its harness
could not see races at all, and rebuilt for sensitivity before trusting anything. Observed values
were printed rather than asserted in every run. One run was handed an unmeasurable claim, was
offered an obvious executable proxy, and refused it explicitly.

Treat absence from this list as weak evidence, and move a row up the moment a run shows it.

| Failure | What it looks like |
|---|---|
| Testing the reimplementation | Writing your own version of the function and testing that instead of importing the library |
| Mocking the thing under test | The mock encodes the assumption, so the test can only confirm it |
| Assertion without observation | `assert result == expected` passes; the actual value is never printed |
| No-error means correct | Script exits 0, so the claim is treated as confirmed, though nothing was checked |
| The easy case only | The claim is tested where it obviously holds, never at the boundary where it might not |
| Single-shot benchmark | One timing run, no warmup, no variance — noise reported as a finding |
| Unfalsifiable null | H₀ hedged ("generally", "in most cases") until no observation could reject it |
| No rival named | H₀ is confirmed without ever being separated from the near-neighbour it is usually confused with |
| Retrofitted claim | The verdict's restatement of H₀ is narrower than the committed wording — check it against the text, not the memory |
| Verdict with no restatement | "Refuted." Refuted *what*? The claim has scrolled away, so nobody re-checks the fit between it and the evidence |
| Absence by failed probe | One probe failed, therefore the feature doesn't exist — see `references/experiment-patterns.md` |
| Open surface treated as closed | An absence claim gets a `Verified` over a space that was never exhaustible — a service, a `__getattr__`, a plugin registry, an unreadable extension. Same error as the row above, opposite direction, and harder to spot because the report looks thorough |
| Citation reported as observation | The vendor's docs agree with the claim, so it's called Verified. Nothing ran; a source was found |
| Untested as a shrug | A barrier is named and the report stops there — no local half run, no source cited, no real trial specified |
| Proxy for the unmeasurable | An inexecutable claim is silently replaced by an adjacent measurable one, and the proxy's result is offered as the verdict |
| Barrier removed by provisioning | Billable or irreversible infrastructure gets created to settle a claim that wasn't worth an invoice |

## Report format

```
## Claim
[The sharpened, falsifiable proposition]

## Hypotheses
H₀: [the claim, strongest form — what this experiment tries to prove false]
H₁: [the most plausible rival if H₀ falls]
Rejected if: [the specific observable that would reject H₀]
             (copied from the message sent in step 2, not composed here)

## Experiment
[Path to the script, and one or two sentences on why this design discriminates]

## Environment
[Language version, library versions, platform — from the script's own output]

## Raw output
[Verbatim]

## Verdict
**[Verified | Refuted | Inconclusive | Untested | Ill-posed]** — scoped to what was actually tested.

H₀ was:       [the committed H₀, verbatim from above — not paraphrased]
Observed:     [the specific value or measurement that decided it]
Now believed: [H₁, or the third thing that turned out true, or H₀ as stated]

## Consequences
[Code, plans, or docs that need correcting. Omit if none.]
```

This block is the final assembly, written after the run. It is not where H₀ is *decided* — step 2 already sent that as its own message, and the Hypotheses section here reproduces it. The two copies being identical is the point: the verdict's restatement can be checked against a message that existed before the run, which is what makes the whole report auditable rather than merely well-formatted.

For a single quick probe, collapse this — but never drop H₀, its falsification condition, the raw output, or the restatement of H₀ in the verdict. Those are what separate this from a confident guess. Collapsing never means merging step 2's message into the final one; a one-line pre-registration sent on its own still costs almost nothing.

## Scope

This version targets standard-library and third-party behavior, where the risk is that the agent's model of someone else's code is wrong.

Claims about code the user controls are a planned extension and the risk profile inverts: the danger is no longer a stale memory but a test that encodes the same misunderstanding as the implementation it's testing. The rule that will matter there is that the test must be derived from the stated requirement, never read off the implementation. Until that's built out, the procedure above still works for user code — just be aware that step 3's "exercise the real library" is doing less protective work.
