# Notes on the autopilot skill

Why `SKILL.md` beside this file is shaped the way it is. None of it is read when the skill runs — `SKILL.md` is what the session executing `start` or `stop` sees, and it holds only what that session has to do. This file is for whoever edits `SKILL.md`, and each note below says what a plausible edit would cost.

## Editing SKILL.md does not reach a running session

The body of `SKILL.md` is read when the skill is invoked, so a change to it needs `/autopilot stop` and `/autopilot start` before it takes effect. A session that solved the issue which changed it and then carried on is still working from the scope it started with, and will report that it has run out of issues rather than that it is reading the wrong set.

## How the reminders fire

A job fires only while the session is idle, never mid-turn, because a turn cannot be preempted. So this skill cannot correct drift inside a task; what it can do is restart a loop that has stalled, which is the failure it is there to catch. It is also why `:07` earns its slot — a session waiting on a run is idle, so that is exactly when a reminder lands, and the answer to it is to keep waiting.

Fire times drift by up to a tenth of the period, a minute here, and the offsets from `:03` on are a minute apart, so `:03` can arrive in the same minute as `:04`. A pair landing together is the tool working as documented, not a job created wrong, and not worth re-spacing the table over.

Both together are why `start` does the work rather than only arming the jobs: the first reminder is up to eleven minutes out, so a session that created the eight and then stopped sits silent for a whole period and looks broken.

## The :05 and :09 reminders are written down nowhere else

`:05` is the one rule `CLAUDE.md` does not carry, and the table in `SKILL.md` is the only copy of it: delete the reminder and the rule leaves the repository with it. `:09` carries the two-section issue form as well as the six-section one, because a reminder that names only one case is read as though that case were the whole rule, and most of the open queue here is workflow and config work. Neither prompt is longer than it needs to be.

## The standing rules live in CLAUDE.md

`CLAUDE.md` at the root of the repository carries verification in CI, committing straight to `main`, the test tiers and the two issue forms, and is read at the start of every turn. `SKILL.md` does not restate any of it — a rule kept in two places drifts with nothing to signal it. The reminders exist for the part `CLAUDE.md` cannot reach: a rule read at the start of a turn is not read again forty minutes into one, and a session that has stopped is not reading anything at all.
