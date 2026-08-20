# prove-it

An agent skill for settling claims about code behavior by running an experiment instead of asserting harder.

When an agent tells you that `sorted()` is stable, that library A handles a case library B
chokes on, or that a parameter defaults to `None`, it is reporting a memory. Memories of API
surfaces go stale, blur across adjacent versions, and confabulate details that are plausible
rather than true — most confidently for well-known libraries, because familiarity is what
produces the confidence, not recall accuracy.

`prove-it` gives you a shorthand for "don't tell me, show me." The claim gets restated as a
null hypothesis, the experiment is designed to reject it, the code runs against the real
library, and the raw output decides.

## Usage

Invoke it against any claim about executable behavior:

> prove it
>
> are you sure `str.strip()` takes a set of characters rather than a substring?
>
> verify that orjson actually handles the datetimes json chokes on
>
> that's a claim about defaults — test it

The skill also fires proactively, before an unverified assumption about library behavior,
version compatibility, or relative performance gets built on.

## What it produces

A saved, re-runnable script; the environment it ran in; verbatim output; and a verdict of
**Verified**, **Refuted**, **Inconclusive**, or **Ill-posed** — scoped to what was actually
tested. See [`examples/`](./examples/) for two full worked cases — a semantic claim and a
performance claim, both refuted.

## Design

The problem this has to solve is that an agent verifying its own claim has a pull toward
writing the test that passes. Three things push back on that:

**The null hypothesis and its falsification condition are written before the code.** H₀ is
the claim itself — stated in the strongest form it will bear, as the thing the experiment
exists to prove false — paired with H₁, the most plausible rival if it falls. Naming the
rival is what makes an experiment discriminating rather than merely confirming; a wrong
model of a function agrees with the right one on ordinary inputs and diverges at the edges.
And a prediction recorded after seeing output can be retrofitted to whatever appeared, while
one recorded before it cannot. Borrowed in spirit from the blind comparator in Anthropic's
`skill-creator`, which withholds version identity from the grader for the same reason.

Note the direction: H₀ is the claim, not the statistical "no effect" default. Rejecting a
boring null would put the agent's motivation on the same side as the experiment's goal. The
claim has to be the thing on trial.

**Observed values get printed, never just asserted.** A passing `assert x == 5` is
indistinguishable from an assertion that was never reached, and tells the reader nothing
about what `x` was.

**The real library gets exercised.** Mocks and reimplementations encode the assumption under
test, so they can only confirm it. This is the single most common way a verification ends up
proving nothing.

Beyond that, `Inconclusive` is treated as a legitimate verdict rather than a failure to be
avoided — the categories where honest verification usually lands there (absence claims,
thread-safety claims) are exactly the ones where manufactured confidence does the most damage.

### Related work

- [`claude-craft/verify-claim`](https://github.com/geigermatic/claude-craft) — general
  claim verification with Verified/Refuted/Inconclusive verdicts and correction at the
  source. Names the experiment that would resolve an inconclusive case but stops short of
  running one; `prove-it` picks up there.
- [`cursor/plugins` `create-verification-skill`](https://github.com/cursor/plugins) —
  generates project-local skills that drive the real app and capture evidence. Oriented
  toward proving an application works rather than settling a specific claim.
- [`claude-fact-checker-skill`](https://github.com/fdaudens/claude-fact-checker-skill) —
  the documentation-and-sources half of the problem. Complementary: use it for claims about
  what the docs say, `prove-it` for claims about what the code does.

## Scope

Currently targeting standard-library and third-party behavior, where the risk is a wrong
model of someone else's code.

Claims about code you control are a planned extension, and the risk inverts: the danger is
no longer a stale memory but a test that encodes the same misunderstanding as the
implementation it checks. The governing rule there will be that the test derives from the
stated requirement, never from reading the implementation.

## Install

### As a plugin (recommended)

The repo doubles as its own single-plugin marketplace. In Claude Code:

```
/plugin marketplace add mdecuir/prove-it
/plugin install prove-it@prove-it
```

Or from the shell:

```bash
claude plugin marketplace add mdecuir/prove-it
claude plugin install prove-it@prove-it
```

Add `--scope project` to either command to commit the marketplace and the plugin to a
project's `.claude/settings.json`, so the whole team picks it up on clone.

Updating:

```bash
claude plugin update prove-it
```

### As a skill

Clone into your skills directory. Claude Code loads any manifest-bearing directory there as
`<name>@skills-dir`, so the same layout works with no plugin install:

```bash
git clone https://github.com/mdecuir/prove-it.git ~/.claude/skills/prove-it
```

Either way, restart Claude Code and confirm the skill was picked up:

```bash
claude plugin details prove-it            # or: prove-it@skills-dir
```

Expected: `Skills (1)  prove-it`. Skills load on invocation — only the description string
sits in the always-on context.

## Layout

```
prove-it/
├── .claude-plugin/
│   ├── plugin.json                     # plugin manifest
│   └── marketplace.json                # single-plugin marketplace, source "./"
├── skills/
│   └── prove-it/
│       ├── SKILL.md                    # procedure, failure modes, report format
│       └── references/
│           └── experiment-patterns.md  # per-claim-type experiment design
└── examples/
    ├── README.md                       # index of worked cases
    ├── utcnow-awareness.md             # semantic claim, refuted
    ├── utcnow_awareness.py
    ├── reread-cost.md                  # performance claim, refuted
    └── reread_cost.py
```

The skill has to live at `skills/<name>/SKILL.md`. A `SKILL.md` at the repo root is not
discovered as a plugin component, even with `"skills": ["./"]` in the manifest — verified
with `claude plugin details`, which reported `Skills (0)` for the root layout and
`Skills (1)` for this one.

## License

MIT
