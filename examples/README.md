# Worked examples

Two end-to-end cases, both captured from real runs. Between them they cover the two
verdicts that carry the most weight and the two claim types that are easiest to fake.

| Case | Claim type | Verdict |
|---|---|---|
| [`utcnow-awareness.md`](./utcnow-awareness.md) | Semantic — what does this return? | **Refuted** |
| [`reread-cost.md`](./reread-cost.md) | Performance — is this cost negligible? | **Refuted** |

The first is the short shape of the procedure: a rival hypothesis that agrees with the
claim on the obvious observable, and a control that separates "the claim is false" from
"the harness is broken."

The second is the long shape. It is a planning assumption rather than a library fact, its
margin has to be committed before the run to mean anything, and the harness itself needed
two corrections before its numbers were trustworthy — both of which are shown rather than
tidied away.

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
