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
