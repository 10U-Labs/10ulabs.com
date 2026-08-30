# Solve what the sweep turns up

## Table of Contents

- [The rule](#the-rule)
- [What needs the user](#what-needs-the-user)
- [The session that produced the first version](#the-session-that-produced-the-first-version)
- [Why the rule was narrowed](#why-the-rule-was-narrowed)
- [A fix that is not yet specifiable](#a-fix-that-is-not-yet-specifiable)
- [What a sweep of five defects does](#what-a-sweep-of-five-defects-does)
- [Related notes](#related-notes)

## The rule

A defect found while working on something else is fixed in the session that found it. It does not go in the reply as a thing noticed, it does not go in a closing paragraph offering to fix it if the user wants, and it does not go in the queue merely because the queue is where work is recorded. A reply is neither a fix nor a record and does not outlive the session; an issue outlives it but costs a second reader a second reading of ground this session already read, and that reader was not in the conversation that found the defect.

## What needs the user

Filing is what happens when the fix needs the user rather than when the defect is inconvenient. Three things need them: a fork only they can settle, a call on scope or priority that is theirs to make, and a change that has to be authorised before it starts. In each case the asking comes first, so that what reaches the queue is the branch that came back rather than the question — [an-issue-states-one-solution](an-issue-states-one-solution.md) is the rule that governs the shape of what is then written. Where the answer arrives inside the session, the fix goes in the session too, and nothing is filed at all.

## The session that produced the first version

The first version of this rule was written on 2026-08-22, at the end of a session that broke it three times. The session began on issue #562, a deleted Glue crawler Lambda with leftovers in the sessions tests. Reading around it turned up more: four tests calling `pytest.skip` or `pytest.fail` in files that never import `pytest`, a `pylint` step reading 207 of the 350 Python files under `test/`, a `mypy` step checking 4.6 per cent of the functions it reads, seven sessions state tests that pass whichever answer AWS gives, and a copy of the shared orphan check written out by hand in the bootstrap tests. Every one of them was found by reading, and every one of them was real. Each reply named one or two and left them unrecorded. The user asked three times, in the same three words, for the issues to be filed, and #571 through #577 are what came out of the third asking.

## Why the rule was narrowed

That version said to file, and filing was the right correction to a session that was leaving findings in replies. It was narrowed on 2026-08-30 because filing is not the cheap half of the choice it looks like. An issue is a handoff, and a handoff costs the next reader everything this session already knows: which files, which run, which line, why it is a defect at all. `72b32527` is the shape the narrowed rule asks for. Answering a push rejected under `#709` turned up twelve conjunction asserts across four files, none of which the rejected commit had touched and three of which no commit had touched in weeks, and all twelve were fixed in the follow-up commit. Filing them would have produced four issues describing findings that a working session already had in front of it, and `e3d194b5` shows why that matters: the thirteenth was found only because the twelve had already been fixed and the run could get far enough to report it.

## A fix that is not yet specifiable

A fix that is not yet specifiable is the work rather than a reason to defer it, and this survives the narrowing unchanged. The check for a test that cannot fail was held back twice as too vague, then specified in one pass once the rule was written against the two real examples in the tree: it fires when every `except` handler either raises or assigns the flag `True`, and stays quiet when a handler can complete with the flag still `False`, which is the difference between the sessions state tests and the correct www authorization tests. Vagueness is a reason to read further, not a reason to hand the reading to somebody else.

## What a sweep of five defects does

A sweep that turns up five defects ends with five fixed, or with an issue for each one the user has to settle, and usually with some of each. Where an issue is written, it is placed in the queue with a `blocked_by` edge only where something genuinely waits on it — see [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md). What is not allowed is the third option: a defect that is real, understood, and left in a reply.

## Related notes

How an issue is written is in [how-issues-are-written](how-issues-are-written.md), the fork that has to be asked about before anything is filed is in [an-issue-states-one-solution](an-issue-states-one-solution.md), and where a filed issue goes in the queue is in [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) and `.claude/skills/autopilot/SKILL.md`.
