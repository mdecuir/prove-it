"""
Claim: `datetime.datetime.utcnow()` returns a timezone-aware datetime in UTC.

Predicted if true:  utcnow().tzinfo is not None, and .utcoffset() == 0:00:00
Refuted if:         utcnow().tzinfo is None (i.e. the object is naive)

Control: datetime.now(timezone.utc), which is documented as aware. If the
control also came back naive, the harness would be at fault rather than the
claim, so it has to be shown alongside.
"""

import datetime
import platform
import sys

print("=== environment ===")
print(f"python   : {sys.version.split()[0]} ({platform.python_implementation()})")
print(f"platform : {platform.platform()}")
print()

print("=== subject: datetime.utcnow() ===")
subject = datetime.datetime.utcnow()
print(f"value    : {subject!r}")
print(f"type     : {type(subject).__name__}")
print(f"tzinfo   : {subject.tzinfo!r}")
print(f"utcoffset: {subject.utcoffset()!r}")
print()

print("=== control: datetime.now(timezone.utc) ===")
control = datetime.datetime.now(datetime.timezone.utc)
print(f"value    : {control!r}")
print(f"tzinfo   : {control.tzinfo!r}")
print(f"utcoffset: {control.utcoffset()!r}")
print()

print("=== consequence probe: subtracting one from the other ===")
try:
    delta = control - subject
    print(f"delta    : {delta!r}")
except TypeError as exc:
    print(f"TypeError: {exc}")
print()

print("=== observed ===")
print(f"subject aware? {subject.tzinfo is not None}")
print(f"control aware? {control.tzinfo is not None}")
