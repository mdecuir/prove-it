# Worked examples

Four end-to-end cases, all captured from real runs.

| Case | Claim type | Verdict |
|---|---|---|
| [`utcnow-awareness.md`](./utcnow-awareness.md) | Semantic — what does this return? | **Refuted** |
| [`reread-cost.md`](./reread-cost.md) | Performance — is this cost negligible? | **Refuted** |
| [`orjson-datetime.md`](./orjson-datetime.md) | Comparative — does A handle what B refuses? | **Verified** |
| [`count-thread-safety.md`](./count-thread-safety.md) | Concurrency — is this safe to share? | **Refuted** |

The first is the short shape of the procedure: a rival hypothesis that agrees with the
claim on the obvious observable, and a control that separates "the claim is false" from
"the harness is broken."

The second is the long shape. It is a planning assumption rather than a library fact, its
margin has to be committed before the run to mean anything, and the harness itself needed
two corrections before its numbers were trustworthy — both of which are shown rather than
tidied away.

The third is the claim that survives, which is the outcome the other three don't show. It is
here because a set of worked examples consisting only of refutations teaches that the procedure
exists to catch people out. What it costs to say `Verified` defensibly — a real attempt to
reject, a control, and a scope narrow enough to be true — is the thing to read it for. It also
carries a breach of the procedure in the run that otherwise followed it most cleanly: the raw
output block was never printed.

The fourth is the category where a clean result is worth the least. H₀ and H₁ predict identical
output on every input a confirming test would reach for, so nearly all the work is proving the
*instrument* can see a race at all — three harness defects, each caught by a pre-registered
falsification condition aimed at the experiment rather than at the claim.

## A caveat about the format

Both cases are single documents. That is not the shape a real run takes, and reading them as
a template would reproduce the one failure the procedure most needs to avoid.

In a run, the Hypotheses block is sent as **its own message before anything executes**, and
the finished report reproduces it afterwards (`SKILL.md` step 2). A write-up collapses that
boundary because a document has no message boundaries to show. The separation is load-bearing,
not cosmetic: a Hypotheses section in a finished report asserts when it was written, while a
message sent ahead of the first run demonstrates it.

So read these as the final assembly, not as a transcript. The pre-registration in each was
sent before the run; the document simply cannot show you that, which is precisely why the
rule is about message order rather than about the report's layout.
