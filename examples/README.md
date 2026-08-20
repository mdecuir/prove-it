# Worked example: a refuted claim

This is what the skill produces end to end. The claim is one an agent could easily
assert in passing, it sounds right, and it is false.

---

## Claim

`datetime.datetime.utcnow()` returns a timezone-aware datetime in UTC, on CPython 3.12.

## Prediction and falsification condition

**Predicted:** `utcnow().tzinfo` is not `None`, and `utcoffset()` returns `timedelta(0)`.

**Refuted if:** `tzinfo` is `None` — the returned object is naive, and its being
nominally "UTC" is a convention about the numbers rather than a property of the object.

## Experiment

[`utcnow_awareness.py`](./utcnow_awareness.py). Calls the real function and prints
`tzinfo` and `utcoffset()` directly rather than asserting on them.

`datetime.now(timezone.utc)` runs as a control. It is documented as aware, so if it
also came back naive the harness would be broken rather than the claim false — those
two outcomes look identical from a single failing probe, which is why the control has
to be in the same run.

The subtraction at the end is a consequence probe: naive and aware datetimes are
non-interoperable in arithmetic, so it turns an abstract type distinction into the
error the user would actually hit.

## Raw output

```
=== environment ===
python   : 3.12.3 (CPython)
platform : Linux-6.18.5-fc-v20-x86_64-with-glibc2.39

=== subject: datetime.utcnow() ===
utcnow_awareness.py:22: DeprecationWarning: datetime.datetime.utcnow() is deprecated
and scheduled for removal in a future version. Use timezone-aware objects to represent
datetimes in UTC: datetime.datetime.now(datetime.UTC).
value    : datetime.datetime(2026, 8, 20, 11, 24, 41, 736358)
type     : datetime
tzinfo   : None
utcoffset: None

=== control: datetime.now(timezone.utc) ===
value    : datetime.datetime(2026, 8, 20, 11, 24, 41, 737289, tzinfo=datetime.timezone.utc)
tzinfo   : datetime.timezone.utc
utcoffset: datetime.timedelta(0)

=== consequence probe: subtracting one from the other ===
TypeError: can't subtract offset-naive and offset-aware datetimes

=== observed ===
subject aware? False
control aware? True
```

## Verdict

**Refuted**, on CPython 3.12.3.

`utcnow()` returns a *naive* datetime whose wall-clock fields happen to be UTC. It
carries no timezone information, so nothing downstream can tell that it is UTC rather
than local time. The control confirms the harness detects awareness correctly, so the
naive result is a property of `utcnow()` and not of the test.

The run also surfaced something the experiment wasn't designed to look for: the
function is deprecated and scheduled for removal, with the standard library itself
pointing at `datetime.now(datetime.UTC)`. Report incidental findings like this —
they were not predicted, which is exactly what makes them worth mentioning.

## Consequences

Any code storing `utcnow()` output alongside aware datetimes will raise `TypeError` on
comparison or subtraction, as the consequence probe shows. The replacement is
`datetime.now(timezone.utc)`.

---

## Why this example

It shows the two things the procedure is built around.

The **control** is what makes a negative result trustworthy. Without it, `tzinfo: None`
is ambiguous between "the claim is false" and "the harness is wrong," and an agent
motivated to confirm its own claim has room to read it the second way.

The **incidental deprecation warning** shows why raw output goes in before
interpretation. An interpretation written first would have summarized to "tzinfo is
None, claim refuted" and dropped the more actionable finding entirely.
