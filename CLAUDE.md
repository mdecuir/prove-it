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

1. **H₀ and its falsification condition committed before the code exists.** The core problem
   is that an agent verifying its own claim is pulled toward writing the test that passes. A
   prediction recorded after seeing output can be retrofitted; one recorded before cannot. If
   this rule erodes, the rest of the skill is theatre.

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

Supporting decision: `Inconclusive` is a first-class verdict. Absence claims and
thread-safety claims genuinely cannot be settled by execution — a failed probe isn't proof
of absence, and clean concurrent runs aren't proof of safety. Manufactured confidence in
those categories is the failure mode worth designing against, so don't "improve" the skill
by making it more decisive there.

## Known weaknesses in the current draft

- **The failure-mode table in `SKILL.md` is reasoned, not observed.** It was written by
  predicting how verifications go wrong, not by watching them go wrong. Expect some entries
  to be irrelevant and some real failures to be missing. Running the skill against real
  claims should reshape this table; treat that as the highest-value next edit.
- **The trigger description is unoptimised.** It was hand-written to be somewhat pushy per
  skill-creator guidance, but never run through the description-tuning loop.
- **No evals exist.** No `evals/evals.json`, no test prompts, no measured trigger rate.
- **Both worked examples are refutations.** There's still no example of a verified claim or
  an inconclusive verdict. `examples/reread-cost.md` covers the performance category (and
  its writeup deliberately keeps both harness bugs visible, because the corrections are the
  instructive part); a comparative two-library case is still missing.

## Next steps, roughly in order

1. Build a test set of claims deliberately mixing outcomes: some that should verify, some
   that should refute, and at least one absence claim and one thread-safety claim that
   *should* land inconclusive. The inconclusive ones matter most — they test whether the
   skill resists manufacturing a verdict.
2. Run the skill against them and rewrite the failure-mode table from what actually happens.
3. Run skill-creator's description optimiser. It needs `claude -p`, which is why it was
   skipped in the originating session:
   ```
   python -m scripts.run_loop --eval-set <trigger-eval.json> --skill-path . \
     --model <model-id> --max-iterations 5 --verbose
   ```
4. Add examples covering a verified verdict and a comparative claim.
5. Only then consider the user-controlled-code extension (see the Scope section of
   `SKILL.md`) — the risk profile inverts there and it deserves its own design pass rather
   than being bolted on.

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
