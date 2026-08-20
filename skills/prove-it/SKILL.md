---
name: prove-it
description: Settle a claim about how code actually behaves by designing, writing, and running a minimal experiment against the real library — then reporting the result even when it refutes the claim. Use whenever someone says "prove it", "are you sure?", "verify that", "show me", "how do you know", or challenges an assertion about what a standard-library or third-party function returns, raises, defaults to, or how two libraries compare. Also use proactively, without being asked, before relying on any unverified assumption about library behavior, version compatibility, or relative performance where the answer is cheap to settle by running code.
---

# Prove It

An assertion about library behavior is a report from memory. Memories of API surfaces go stale, blur across adjacent versions, and confabulate details that are plausible rather than true — and they do it most confidently for libraries that are well known, because familiarity is what generates the confidence, not recall accuracy.

This skill replaces the assertion with an experiment. The claim gets restated as something that could be false, an experiment gets designed that could show it false, the code runs against the real library, and the raw output decides.

The load-bearing property is that **the experiment must be able to refute the claim**. An agent testing its own assertion has an obvious pull toward writing the test that passes. Everything below is structured to make that harder.

## What this applies to

Settle by execution: return values, raised exceptions, default arguments, ordering and stability guarantees, mutation vs. copy semantics, encoding and coercion behavior, version compatibility, and relative performance between two concrete options.

Do not use execution for: what the documentation *recommends*, design and style questions, claims about a library's roadmap, or claims about a system you have no access to. Say the claim isn't executable and offer the appropriate alternative — usually a documentation lookup with a citation. A fabricated experiment is far worse than an honest "I can't test that from here."

## Procedure

### 1. Restate the claim as a falsifiable proposition

The original assertion is usually too loose to test. Sharpen it, and show the sharpened version — the user needs to see what is actually about to be tested, because the gap between what was said and what gets tested is where bad verifications hide.

A testable proposition names: the exact call or operation, the exact input, the expected observable, and the environment it's claimed to hold in. "`sorted()` is stable" becomes "`sorted()` in CPython 3.12 preserves the relative order of elements comparing equal under the supplied key."

Behavior claims are always claims about a *(library, version)* pair. If the version is unstated, either pin the one the user's project actually uses or test across the plausible range and say which is which.

If sharpening changes the meaning of the claim, flag it and ask. Quietly testing a weaker proposition than the one asserted is a way of appearing to verify while verifying nothing.

### 2. State the null hypothesis, its rival, and the falsification condition — before writing any code

Write all three, in the response, before the script exists:

- **H₀ (null hypothesis):** the claim, in the strongest form it will bear. This is the proposition the experiment exists to prove false.
- **H₁ (rival):** the most plausible thing that is true instead, if H₀ falls.
- **Falsification condition:** the specific observable that would reject H₀.

H₀ here is the claim itself, not the statistical "no effect" default. The inversion is deliberate and load-bearing: an experiment that sets out to reject its own assertion is working against the agent's bias, whereas one that sets out to reject a boring null is working with it. Keep the claim on trial. (For performance and comparative claims the claim *is* the effect, so H₀ is "A is faster than B by margin M" and H₁ is "the difference sits inside run-to-run variance." Same rule, and it is what gives the variance requirement in `references/experiment-patterns.md` its teeth.)

Naming H₁ is what makes an experiment *discriminating* rather than merely confirming. A wrong model of a function usually agrees with the right one on ordinary inputs and diverges only at the edges, so the input worth running is the one that separates H₀ from H₁ — not the one that shows H₀ working. "`str.strip()` takes a set of characters" has the rival "it takes a substring," and the two agree on nearly every input a confirming test would reach for.

Stating H₀ in its strongest form is the anti-retrofit device. A hedged null survives anything, and if a refuting result later prompts a narrower claim, the narrowing is visibly a *different* H₀ rather than the same one clarified.

This ordering is the whole mechanism. A prediction recorded after seeing output can be retrofitted to whatever appeared; one recorded before it cannot. It converts "the test passed" into a statement with content.

If no observable can be named that would reject H₀, stop. The claim is either vacuous, or not empirical, or not yet sharpened. Return to step 1 or say so plainly.

### 3. Design the minimal discriminating experiment

- **Exercise the real library.** Import and call the actual thing. A reimplementation, a mock, or a stub tests your model of the library, which is exactly the thing under suspicion. This is the single most common way an experiment ends up proving nothing.
- **Vary one thing.** For comparison claims, both options run through the same harness on the same inputs, with only the option under comparison differing.
- **Probe the boundary the claim depends on.** A claim about behavior at a threshold is tested at the threshold, on both sides. A claim that holds only in the easy case is not the claim that was made.
- **Include the near-miss case.** If the claim is "X raises on empty input," also run the non-empty input. Without it, a script that raises for an unrelated reason looks like confirmation.
- **Keep it small.** A twenty-line script that the user can read in one pass and re-run themselves is worth more than a thorough harness they have to trust.

Per-claim-type recipes — semantic, comparative, performance, exception, version-compatibility, and absence claims — are in `references/experiment-patterns.md`. Read it when the claim type isn't a straightforward "what does this return."

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
- **Ill-posed** — the claim can't be made falsifiable. Explain what's ambiguous.

### 7. Follow through to the source

A refuted claim usually has descendants. Find them:

- Code already written on the assumption — fix it or flag it.
- A plan or design decision that rested on it — reopen it.
- A doc, comment, or memory file that records it — correct it there, or the same wrong claim returns next session.

## Failure modes

These are the ways a verification produces a green result while proving nothing. Check against them before reporting.

| Failure | What it looks like |
|---|---|
| Testing the reimplementation | Writing your own version of the function and testing that instead of importing the library |
| Mocking the thing under test | The mock encodes the assumption, so the test can only confirm it |
| Assertion without observation | `assert result == expected` passes; the actual value is never printed |
| No-error means correct | Script exits 0, so the claim is treated as confirmed, though nothing was checked |
| Version drift | Claim was about v2; the environment silently resolved v3 |
| The easy case only | The claim is tested where it obviously holds, never at the boundary where it might not |
| Single-shot benchmark | One timing run, no warmup, no variance — noise reported as a finding |
| Unfalsifiable null | H₀ hedged ("generally", "in most cases") until no observation could reject it |
| No rival named | H₀ is confirmed without ever being separated from the near-neighbour it is usually confused with |
| Retrofitted claim | The verdict's restatement of H₀ is narrower than the committed wording — check it against the text, not the memory |
| Verdict with no restatement | "Refuted." Refuted *what*? The claim has scrolled away, so nobody re-checks the fit between it and the evidence |
| Absence by failed probe | One probe failed, therefore the feature doesn't exist — see `references/experiment-patterns.md` |

## Report format

```
## Claim
[The sharpened, falsifiable proposition]

## Hypotheses
H₀: [the claim, strongest form — what this experiment tries to prove false]
H₁: [the most plausible rival if H₀ falls]
Rejected if: [the specific observable that would reject H₀]

## Experiment
[Path to the script, and one or two sentences on why this design discriminates]

## Environment
[Language version, library versions, platform — from the script's own output]

## Raw output
[Verbatim]

## Verdict
**[Verified | Refuted | Inconclusive | Ill-posed]** — scoped to what was actually tested.

H₀ was:       [the committed H₀, verbatim from above — not paraphrased]
Observed:     [the specific value or measurement that decided it]
Now believed: [H₁, or the third thing that turned out true, or H₀ as stated]

## Consequences
[Code, plans, or docs that need correcting. Omit if none.]
```

For a single quick probe, collapse this — but never drop H₀, its falsification condition, the raw output, or the restatement of H₀ in the verdict. Those are what separate this from a confident guess.

## Scope

This version targets standard-library and third-party behavior, where the risk is that the agent's model of someone else's code is wrong.

Claims about code the user controls are a planned extension and the risk profile inverts: the danger is no longer a stale memory but a test that encodes the same misunderstanding as the implementation it's testing. The rule that will matter there is that the test must be derived from the stated requirement, never read off the implementation. Until that's built out, the procedure above still works for user code — just be aware that step 3's "exercise the real library" is doing less protective work.
