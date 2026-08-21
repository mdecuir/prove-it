# Worked example: does orjson serialize datetimes that stdlib `json` refuses?

**Claim, as stated:** "orjson serializes datetime objects that plain json chokes on. Verify that."

**Claim type:** comparative — two libraries, same input, one observable.
**Verdict:** **Verified**, scoped to CPython 3.14.7 / orjson 3.12.0.

This is the example of a claim that *survives*. It is here because a skill whose only worked
cases are refutations teaches the wrong lesson: that the procedure exists to catch people out.
It exists to settle claims. Sometimes the claim is right, and then the interesting question is
what a defensible `Verified` costs — a real attempt to reject, a control that separates the
result from a broken harness, and a scope narrow enough to be true.

---

## Sharpened claim

`json.dumps({"t": datetime.datetime(...)})` from CPython's stdlib raises `TypeError`, while
`orjson.dumps` on the same dict returns bytes containing an RFC 3339 timestamp string — no
custom `default=` handler in either case.

"Chokes on" became "raises `TypeError`", and "serializes" became "returns bytes containing an
RFC 3339 string". Both were vague enough to be unfalsifiable as stated: a library that
returned `"datetime.datetime(2026, 8, 21, ...)"` would also have "serialized" the object.

## Pre-registration

Sent as its own message, before anything ran.

**H₀:** For a naive and an aware `datetime.datetime`, plus `date` and `time`, stdlib
`json.dumps(obj)` raises `TypeError` and `orjson.dumps(obj)` returns bytes with an RFC 3339 /
ISO 8601 string.

**H₁:** orjson does *not* handle these natively either (raises
`orjson.JSONEncodeError`/`TypeError` absent a `default=`), and the memory is of a `default=`
recipe rather than built-in support. Weaker rival: it handles `datetime` but not `date`/`time`.

**Rejected if:** any of the four types raises from `orjson.dumps` without a `default=`, **or**
stdlib `json.dumps` *succeeds* on any of them.

**Near-miss control:** both libraries must succeed on a plain `{"t": "2026-08-21"}` string
dict, proving the failure is datetime-specific and not a broken harness.

Two things about that H₁ are worth copying. It is not "the claim is false" — it names the
specific way a true-feeling memory goes wrong, which is remembering a `default=` recipe you
once wrote and attributing its effect to the library. And the weaker rival ("`datetime` yes,
`date`/`time` no") is what makes the input set four types instead of one: on a single naive
`datetime`, H₀ and the weaker rival agree, so that test discriminates nothing.

## Experiment

Both libraries get the same `obj` through the same loop, in a throwaway venv. Nineteen lines.

```python
import sys, json, platform, datetime, orjson

print("python:", sys.version.split()[0])
print("orjson:", orjson.__version__)
print("platform:", platform.platform())
print()

cases = {
    "datetime-naive": datetime.datetime(2026, 8, 21, 13, 45, 30, 123456),
    "datetime-aware": datetime.datetime(2026, 8, 21, 13, 45, 30, tzinfo=datetime.timezone.utc),
    "date":           datetime.date(2026, 8, 21),
    "time":           datetime.time(13, 45, 30),
    "CONTROL-str":    "2026-08-21",  # near-miss: both must succeed
}

for name, val in cases.items():
    obj = {"t": val}
    for lib in (json, orjson):
        try:
            out = lib.dumps(obj)
        except Exception as e:
            print(f"{name:15} {lib.__name__:7} RAISED {type(e).__name__}: {e}")
        else:
            print(f"{name:15} {lib.__name__:7} OK     {out!r}")
    print()
```

`lib.dumps(obj)` with `lib` from a tuple is the whole "vary one thing" rule made mechanical:
there is no place to accidentally pass `default=` to one arm and not the other, because there
is only one call site.

The printed `repr` of the result matters as much as the OK/RAISED. "orjson serialized it" is
compatible with orjson emitting an epoch float or a `repr`; only the bytes settle whether the
output is RFC 3339.

## Raw output

```
python: 3.14.7
orjson: 3.12.0
platform: macOS-26.5.2-arm64-arm-64bit-Mach-O

datetime-naive  json    RAISED TypeError: Object of type datetime is not JSON serializable
datetime-naive  orjson  OK     b'{"t":"2026-08-21T13:45:30.123456"}'

datetime-aware  json    RAISED TypeError: Object of type datetime is not JSON serializable
datetime-aware  orjson  OK     b'{"t":"2026-08-21T13:45:30+00:00"}'

date            json    RAISED TypeError: Object of type date is not JSON serializable
date            orjson  OK     b'{"t":"2026-08-21"}'

time            json    RAISED TypeError: Object of type time is not JSON serializable
time            orjson  OK     b'{"t":"13:45:30"}'

CONTROL-str     json    OK     '{"t": "2026-08-21"}'
CONTROL-str     orjson  OK     b'{"t":"2026-08-21"}'
```

## Verdict

**Verified** — CPython 3.14.7, orjson 3.12.0, macOS arm64.

**H₀ was:** "For a naive and an aware `datetime.datetime`, plus `date` and `time`, stdlib
`json.dumps(obj)` raises `TypeError` and `orjson.dumps(obj)` returns bytes with an RFC 3339 /
ISO 8601 string."

**Observed:** all four types raised `TypeError: Object of type <T> is not JSON serializable`
from stdlib json; all four serialized from orjson with no `default=`. The control string dict
succeeded in both, so the stdlib failures are datetime-specific rather than harness breakage.

**Now believed:** H₀ as stated. H₁ rejected — no `default=` is involved anywhere in the orjson
arm.

Strictly this is *failed to reject*, which is why the version stamp is part of the verdict
rather than a footnote. "orjson handles datetimes" is a claim about every orjson; what ran
here was one.

## Two details the claim did not mention

Both are visible in the output above, and neither was asked about:

- The aware datetime renders `+00:00`, not `Z`. Pass `orjson.OPT_UTC_Z` if a consumer demands
  `Z`.
- The naive datetime serializes silently, with no offset and no complaint. orjson does not make
  you think about tz-awareness; `OPT_NAIVE_UTC` stamps naive values as UTC if that is what you
  meant.

The second is the one worth carrying, because it interacts with the other worked example here:
[`utcnow-awareness.md`](./utcnow-awareness.md) is about naive datetimes being produced without
anyone noticing. orjson will happily write one into your API response.

## What this run did wrong

It did not print the raw output block. The verdict above summarised the output in prose
("all four types raised…") and the actual printed lines never appeared in the report — they are
in this document only because the transcript's tool result still had them. That is `SKILL.md`
step 5 breached, in the run that otherwise followed the procedure most cleanly, and it is
recorded in `evals/results-2026-08-21.md` rather than tidied away. A `Verified` whose evidence
is a paraphrase of the evidence is the exact shape this skill exists to refuse.
