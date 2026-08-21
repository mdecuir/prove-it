# Project context

`prove-it` is an agent skill that settles claims about code behavior by designing and
running an experiment rather than asserting harder. It was drafted in a claude.ai session
that had no access to this repo directory; this file carries that context over.

Read `README.md` for the pitch and `skills/prove-it/SKILL.md` for the skill itself before
changing anything.

## Origin

The search that preceded the draft found adjacent tools but nothing doing this specific job:

- `claude-craft/verify-claim` — verdict vocabulary and correction-at-source. Names the
  experiment that would resolve an inconclusive case but doesn't run one.
- `cursor/plugins` `create-verification-skill` — generates project-local skills that drive
  the real app. Oriented toward "prove this app works," not "settle this claim."
- `claude-fact-checker-skill` — the documentation half. Complementary rather than
  overlapping.
- Anthropic's `skill-creator` — its blind comparator (grader doesn't know which version
  produced which output) is the conceptual ancestor of the falsification-condition rule.

The gap was the triggering-and-scoping layer: classify a claim as empirically testable,
design the minimal discriminating experiment, run it, and report the result even when it
contradicts what the agent said a moment ago.

## Load-bearing design decisions

Three, in descending order of how much the skill depends on them:

1. **H₀ and its falsification condition committed, as their own message, before anything runs.**
   The core problem is that an agent verifying its own claim is pulled toward writing the test
   that passes. A prediction recorded after seeing output can be retrofitted; one recorded before
   cannot. If this rule erodes, the rest of the skill is theatre.

   The wording matters and was corrected once already. "Before the code exists" is the wrong line
   — drafting a script then pre-registering before executing it is fine. And a Hypotheses
   *section* in the finished report proves nothing about when it was written, which is how run 1
   produced three reports that looked exemplary and were composed backwards. The rule has to be
   about message order, because that is the only part of it that is observable.

   The direction of H₀ is itself load-bearing and easy to "fix" wrongly: **H₀ is the claim**,
   not the statistical no-effect null. Flipping it to convention would put the agent's
   motivation on the same side as the experiment's goal — rejecting "no difference" is just
   confirming your own assertion with extra steps. The performance section of
   `references/experiment-patterns.md` is the one place the two coincide, because there the
   claim *is* the effect.

   H₁ (the most plausible rival) was added alongside for a separate reason: a falsification
   condition names a *result*, while a rival names the thing you would be *wrong about*, and
   only the latter tells you which input to choose. Dropping H₁ back out would leave the
   skill confirming claims against inputs where every candidate model agrees.

2. **Observed values printed, never merely asserted.** A passing `assert x == 5` is
   indistinguishable from an assertion that was never reached.

3. **The real library is exercised.** Mocks and reimplementations encode the assumption
   under test and can only confirm it.

Supporting decision: the non-`Verified` verdicts are first-class. `Inconclusive` exists
because absence claims and thread-safety claims genuinely cannot be settled by execution — a
failed probe isn't proof of absence, and clean concurrent runs aren't proof of safety.
Manufactured confidence in those categories is the failure mode worth designing against, so
don't "improve" the skill by making it more decisive there.

`Untested` was added later, for the claim that is empirical and would be settled by a real
experiment that simply can't be run from here — cost, scale, production access, wall-clock.
It is deliberately expensive to reach: a barrier from a closed list, plus a three-part
decomposition (run the local half, cite the remote half *as sourced*, name the smallest real
trial). Without that it degenerates into the cheapest verdict in the set, because it always
sounds reasonable. The hard guardrail alongside it — never provision billable or irreversible
resources to settle a claim — exists because this skill's whole instinct is "just run it", and
that instinct is actively dangerous once a cloud account is in reach.

## Known weaknesses in the current draft

- **The failure-mode table in `SKILL.md` is still the predicted one.** Run 1 (2026-08-20)
  produced the evidence to rewrite it but the rewrite has not been applied — see the pending
  list below. Four predicted rows were not observed once in twelve runs, and five real failures
  are missing from it.
- **The trigger description is unoptimised.** It was hand-written to be somewhat pushy per
  skill-creator guidance, but never run through the description-tuning loop.
- **The test set has been run once, n=1 per case.** `evals/test-claims.md` plus
  `evals/results-2026-08-20.md`. Nothing in those results is a rate, and the ponytail confound
  (below) is only partly controlled. It is markdown rather than `evals/**/case.yaml` because
  `claude plugin eval` is gated behind early access on this account and its schema couldn't be
  read from the tool; `claude plugin eval init --bare` just prints the gate message.
- **Both worked examples are refutations.** There's still no example of a verified claim or
  an inconclusive verdict. `examples/reread-cost.md` covers the performance category (and
  its writeup deliberately keeps both harness bugs visible, because the corrections are the
  instructive part); a comparative two-library case is still missing.

## Reproducing a run

The harness is three flags and two gotchas. Both gotchas cost real time in run 1.

```bash
# marketplace.json MUST be absent from the copy, or --plugin-dir silently loads nothing
rsync -a --exclude .git --exclude evals <repo>/ /tmp/plugin-only/
rm /tmp/plugin-only/.claude-plugin/marketplace.json

claude -p --plugin-dir /tmp/plugin-only --model claude-opus-5 \
  --allowedTools Bash Write Read Edit Glob Grep \
  --output-format stream-json --verbose "<the claim, as a user would say it>"
```

- **`stream-json` is not optional.** The final message can contain a perfectly ordered report
  while the transcript shows H₀ was written after the output existed. Only the event stream
  distinguishes those, and that is the main thing this skill needs measured.
- **`--permission-mode bypassPermissions` is refused** by the auto-mode classifier. The
  explicit `--allowedTools` list works.
- **`CLAUDE_CONFIG_DIR` isolation breaks auth**, so subprocesses inherit the operator's other
  plugins. On this machine that means `ponytail`, whose "code first, at most three short lines"
  rule directly contradicts this skill's pre-registration requirement. Prefix a prompt with
  `normal mode.` to disable it for a control arm.
- **Neutralize cloud credentials** before the `untested-managed-bulk-load` case. Run 1 verified
  the neutralization by confirming `aws sts get-caller-identity` returns `NoCredentials` first.
- **Pin `--model`.** Runs 1 and 2 did not, which left the two non-comparable until the model was
  recovered from `modelUsage` in the transcripts after the fact. That is the *version drift* row
  of the skill's own failure table, committed twice in the skill's own evaluation.
- **Invocation is unreliable, so n=1 proves nothing about triggering.** The same prompt fired the
  skill 3/3 in run 1 and 0/4 in run 2. Any claim about whether a description change works needs
  at least two reps per case and a same-conditions arm with the old description.

## Next steps, roughly in order

Run 1 is done. These are the edits it justified; the evidence for each is in
`evals/results-2026-08-20.md` under the numbered finding cited. Item 1 is applied, 2–4 are not.

1. ~~Reword step 2's ordering rule to what it actually protects (finding 1).~~ **Done and
   verified.** Step 2 is now "before anything runs" plus an explicit "as its own message"
   requirement, argued from observability rather than discipline: a Hypotheses *section* asserts
   when it was written and cannot be checked, while a message ahead of the first run demonstrates
   it. The report format says the Hypotheses block is copied from that message, and
   `examples/README.md` warns that both worked examples are single documents and must not be read
   as transcripts.

   Verified in run 2 under explicit invocation: 4 of 4 runs pre-registered before writing or
   running anything, against 3 of 9 composing H₀ after the output in run 1. n=4, one claim type
   — the mechanism works, the effect size is unknown.
2. **Rewrite the failure-mode table into two tables (findings 1–3, 8).** Observed, with the case
   that showed it; and predicted-but-unseen, marked as such. Add rows for: report-in-one-message,
   vendor facts asserted without citation because triage never ran, and skill not firing at all.
   Do not delete the four unobserved rows — twelve runs is too few — but stop presenting them as
   equals of the observed ones.
3. ~~Fix the trigger description (findings 2, 3).~~ **Rewritten, and then descoped.** The old
   description promised "designing, writing, and running a minimal experiment," so a claim that
   cannot be run read as out of scope — triage, `Untested`, and `Ill-posed` were never advertised
   in the one string that decides invocation. The new description leads with classification and
   names all three routes, and fired 4/4 where the old one had been 0/2 on cost claims.

   **But it is not established as the fix**, and triggering is no longer in scope for the evals.
   An isolation arm (old description, model pinned) fired 1 of 2, which against 2 of 2 is not a
   result — and two variables had changed at once anyway. Automatic firing proved unreliable
   enough (3/3 in run 1, 0/4 in run 2, including a prompt ending in the literal words "Prove it.")
   that it was blocking every other measurement. `evals/test-claims.md` and the README now require
   explicit `/prove-it` invocation, and proactive firing is documented as intended but
   undependable.

   **Still open as its own question:** make automatic invocation dependable. It needs a
   trigger-only eval — many prompts, several reps each, scored purely on whether the skill loads —
   which is a different instrument from `test-claims.md`. Do not fold it back in.
4. **Split closed from open surfaces in the absence-claims reference (finding 5).** A stdlib
   module whose source you can read end to end is not the same problem as a service or a library
   with dynamic attributes. `Verified` is reachable for the first by enumerate-and-read; only the
   second is inherently `Inconclusive`. Run 1's `zipfile` case did this correctly and the
   reference did not describe it.
5. Re-run the set after 1–4 to see which findings move, and add the missing comparative and
   verified worked examples. `inconclusive-itertools-count-threadsafe` is a candidate worked
   example in its own right (finding 7) — it is the best run of the set and the only observed
   evidence that the concurrency guidance works.
6. Only then consider the user-controlled-code extension (see the Scope section of `SKILL.md`) —
   the risk profile inverts there and it deserves its own design pass rather than being bolted
   on.

### On the description optimiser

Folded into step 3 above. Note that skill-creator is **not actually installed** on this machine
— `~/.claude/skills/skill-creator` is a dangling symlink to `~/.agents/skills/skill-creator`,
which does not exist. Its eval-set schema could not be read, so the loop below is from the
originating session's notes rather than verified here:

```
python -m scripts.run_loop --eval-set <trigger-eval.json> --skill-path . \
  --model <model-id> --max-iterations 5 --verbose
```

The trigger cases run 1 established as failing (cost/infrastructure, pure preference) are the
ones any optimiser run should be seeded with.

## Packaging

The repo is both a plugin and its own single-plugin marketplace: `.claude-plugin/plugin.json`
plus `.claude-plugin/marketplace.json` with `source: "./"`. That one layout serves both
install paths — `/plugin install prove-it@prove-it`, and cloning into `~/.claude/skills/prove-it`
where it loads as `prove-it@skills-dir`.

Two things were established by running `claude plugin details` rather than by assumption, and
both are easy to break:

- **The skill must live at `skills/prove-it/SKILL.md`.** A root-level `SKILL.md` is *not*
  discovered as a plugin component, even with `"skills": ["./"]` in the manifest — that is
  what `claude plugin init` scaffolds, and its own root `SKILL.md` reports `Skills (0)`.
  Root `SKILL.md` only works for the older bare-skill-directory convention.
- **Versions in `plugin.json` and the `marketplace.json` entry must agree.**
  `claude plugin tag` refuses to cut a release tag when they drift, so bump both.

`claude plugin validate .` checks the manifests. It validates whichever manifest it finds
first, so point it at `.claude-plugin/plugin.json` explicitly to check that one. It warns that
this file, `CLAUDE.md`, is not loaded as plugin context — that is correct and intended; it is
repo context for whoever edits the skill, not part of the shipped plugin.

## Conventions

- `SKILL.md` stays under ~500 lines; depth goes into `references/`.
- Explain *why* a rule exists rather than issuing bare MUSTs — the skill is read by a model
  that follows reasoning better than commands.
- Example scripts are real and actually run. Captured output stays verbatim, including the
  parts nobody predicted — the deprecation warning in `examples/utcnow-awareness.md` and the
  odd cheaper-than-parse timing in `examples/reread-cost.md` both survive because they
  illustrate why raw output precedes interpretation. Don't replace captured output with
  plausible-looking output.

- `examples/reread_cost.py` needs polars, so it is not runnable from a bare checkout. Its
  docstring carries the throwaway-venv invocation, per the skill's own step 4. If you re-run
  it, expect different absolute timings and replace the whole captured block rather than
  editing numbers inside it.
