# File what the sweep turns up

## Table of Contents

- [The rule](#the-rule)
- [The session that produced it](#the-session-that-produced-it)
- [Two reasons that look responsible](#two-reasons-that-look-responsible)
- [A fork in how to fix it](#a-fork-in-how-to-fix-it)
- [A fix that is not yet specifiable](#a-fix-that-is-not-yet-specifiable)
- [What a sweep of five defects does](#what-a-sweep-of-five-defects-does)
- [Related notes](#related-notes)

## The rule

A defect found while working on something else is filed in the same turn it is found. It does not go in the reply as a thing noticed, and it does not go in a closing paragraph offering to file it if the user wants. The queue is where work is recorded. A reply is not, and a defect named only in a reply is gone when the session ends.

## The session that produced it

This rule was written on 2026-08-22, at the end of a session that broke it three times. The session began on issue #562, a deleted Glue crawler Lambda with leftovers in the sessions tests. Reading around it turned up more: four tests calling `pytest.skip` or `pytest.fail` in files that never import `pytest`, a `pylint` step reading 207 of the 350 Python files under `test/`, a `mypy` step checking 4.6 per cent of the functions it reads, seven sessions state tests that pass whichever answer AWS gives, and a copy of the shared orphan check written out by hand in the bootstrap tests. Every one of them was found by reading, and every one of them was real. Each reply named one or two and left them unfiled. The user asked three times, in the same three words, for the issues to be filed, and #571 through #577 are what came out of the third asking.

## Two reasons that look responsible

Two reasons for holding one back both look responsible and are not.

## A fork in how to fix it

The first is that the fix has a fork in it. That is a reason to ask which branch and then file, which is what [an-issue-states-one-solution](an-issue-states-one-solution.md) already says; the asking belongs in front of the filing, as a step inside it, rather than in place of it. A fork in how to fix a defect says nothing about whether the defect is real, and the defect is what the issue records. Where the repository already settles the fork, settle it and name the rejected branch and why it lost: #576 keeps the bootstrap cold-state skip and folds the duplicate into the shared helper because six subsystems already call that helper, and the branch that kept both copies is named in the body.

## A fix that is not yet specifiable

The second is that the fix is not yet specifiable. That is the work rather than a reason to defer it. The check for a test that cannot fail was held back twice as too vague, then specified in one pass once the rule was written against the two real examples in the tree: it fires when every `except` handler either raises or assigns the flag `True`, and stays quiet when a handler can complete with the flag still `False`, which is the difference between the sessions state tests and the correct www authorization tests. Where something genuinely cannot be pinned down, the sentence saying so belongs in the issue's own `Proposed Solution`, where whoever picks it up will read it.

## What a sweep of five defects does

A sweep that turns up five defects files five issues in the turn that found them, each with a `blocked_by` edge where something genuinely waits on it and none where nothing does — see [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md). Filing is cheap, an issue is editable, and a wrong issue is corrected by the next reader; a defect held in a reply is corrected by nobody.

## Related notes

How an issue is written is in [how-issues-are-written](how-issues-are-written.md), and where a filed issue goes in the queue is in [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) and `.claude/skills/autopilot/SKILL.md`.
