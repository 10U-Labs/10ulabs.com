---
name: autopilot
description: Start or stop the standing reminders that keep an autonomous issue-solving session on the rails. Use when the user says "start autopilot", "go autonomous on the open issues", "stop autopilot", or asks to clear the reminders. Takes "start" or "stop".
---

## Table of Contents

- [Overview](#overview)
- [Sub-Commands](#sub-commands)
  - [Start](#start)
    - [Scope](#scope)
    - [Create the reminders](#create-the-reminders)
    - [Start working](#start-working)
    - [Place a filed issue](#place-a-filed-issue)
  - [Stop](#stop)
- [Notes](#notes)
  - [Editing this file does not reach a running session](#editing-this-file-does-not-reach-a-running-session)
  - [How the reminders fire](#how-the-reminders-fire)
  - [The :05 and :09 reminders are written down nowhere else](#the-05-and-09-reminders-are-written-down-nowhere-else)
  - [The standing rules live in CLAUDE.md](#the-standing-rules-live-in-claudemd)

## Overview

Eight recurring reminders, one per standing rule, that fire back into this session while it works through the open issues on `10U-Labs/10ulabs.com` on its own. One reminder per rule, so no rule can be quietly dropped from a merged block of text; staggered across a ten-minute period so they arrive spread out rather than as a wall.

The argument is the sub-command, `start` or `stop`. Neither takes anything else — `start` reads its scope out of the repository.

`CronCreate`, `CronList` and `CronDelete` are deferred tools: the session is told their names but not their schemas, so a call made before the schema is fetched fails with `InputValidationError` and creates nothing. Fetch them first with `ToolSearch`, query `select:CronCreate,CronList,CronDelete`.

## Sub-Commands

### Start

#### Scope

Every open issue in this repository is in scope, and so is every open issue reached by following a dependency out of that set, whatever its number and whatever repository it lives in — `1e45d1f9` closed an issue in another repository for exactly that reason. `start` takes no issue number: a number can only be a floor, a floor only excludes issues by age, and an issue's number says nothing about whether it has to be done, least of all across repositories where the numbering is unrelated. If the user names a number anyway, they are asking to start rather than to narrow; say the whole open set is in scope and start.

#### Create the reminders

Create eight jobs with `CronCreate`, exactly as listed. Use `recurring: true` (the default), and take the prompts verbatim; none of them has anything to substitute. Each `cron` field is a distinct offset within the same ten-minute period.

| Offset | Cron | Prompt |
| --- | --- | --- |
| :01 | `1,11,21,31,41,51 * * * *` | `REMINDER: Continue to solve the open issues autonomously, unless you need human feedback about ANYTHING — not just about the next open issue.` |
| :03 | `3,13,23,33,43,53 * * * *` | `REMINDER: Issues must be solved through a single commit & push.` |
| :04 | `4,14,24,34,44,54 * * * *` | `REMINDER: Issues must be solved through a set of indivisible Claude tasks.` |
| :05 | `5,15,25,35,45,55 * * * *` | `REMINDER: Lead with what the thing is for. Every paragraph — in chat as much as in issues, commits and comments — opens with a plain sentence saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top, not in the seventh paragraph. Then cut the details that change nothing the reader would do.` |
| :06 | `6,16,26,36,46,56 * * * *` | `REMINDER: Ensure Claude tasks are indivisible.` |
| :07 | `7,17,27,37,47,57 * * * *` | `REMINDER: Do not do anything but wait while a workflow is running.` |
| :08 | `8,18,28,38,48,58 * * * *` | `REMINDER: An issue you file goes into the sequence before you go back to work. Add a blocked_by edge: the issue in hand is blocked by the new one if it cannot be finished without it, otherwise whichever issue in the set cannot be finished without it, otherwise the new issue is blocked by the tail of the sequence. Never leave a filed issue with no edge.` |
| :09 | `9,19,29,39,49,59 * * * *` | `REMINDER: When you come up against a new problem, file a GitHub issue. A problem in the program — src/, lib/python/, lib/terraform/, scripts/ — gets the sub-headers "Problem", "Why Unit Tests Did Not Catch It", "Why Integration Tests Did Not Catch It", "Why E2E Tests Did Not Catch It", "Which Unit, Integration, or E2E regression tests would prevent this from happening again?", and "Proposed Solution". A problem in a config, a map, a workflow file or the docs — etc/, .github/, docs/, products/ — gets "Problem" and "Proposed Solution" only, and owes no tests.` |

Then tell the user that eight reminders are running, how many open issues are in scope, and the two limits that come with them: the jobs live in this session only and are gone when it ends, and recurring jobs auto-expire after seven days.

#### Start working

Start in the same turn that created the jobs. Running this skill is starting the work; the eight jobs only keep it on the rails once it is going.

Read the open issues with `gh issue list`, then read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each of them; every entry names the repository its blocker lives in. Follow those entries, and the entries of the issues they reach, until nothing new comes back, and add every open issue found this way to the set. Then take the lowest-numbered issue in the set that no open issue blocks, preferring this repository when two are equally unblocked, and solve it under the standing rules the reminders carry — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it.

#### Place a filed issue

An issue filed during a run goes into the sequence before the session goes back to work. A `blocked_by` edge points from the issue that waits to the issue it waits on, and three cases cover everything:

- The issue in hand cannot be finished until the new one is: the issue in hand gets the new one as a `blocked_by`, which puts the new issue immediately in front of it, and in front of the whole sequence when the issue in hand is its head.
- Some other issue in the set cannot be finished until the new one is: that issue gets the new one as a `blocked_by`.
- Neither: the new issue gets an edge to the tail of the sequence, the one open issue in the set that no other open issue is blocked by.

There is no fourth case and nothing to choose between — an issue is either needed before something already in the sequence or it is not. Never leave a filed issue without an edge: with no edge it is worked last in this repository, because it carries the highest number and the tie-break above takes the lowest, and in another repository it is never reached at all, because the traversal gets there only by following an edge into it.

Read the tail rather than remembering it, because issues are filed here in batches and the tail moves with them. `gh issue view <n>` prints a `blocked-by` and a `blocking` line, which is enough to place a new issue without walking the API twice.

Add the edge with `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F issue_id=<id>`, where `{number}` is the issue that waits and `<id>` is the numeric id of the blocker, read from `gh api repos/{owner}/{repo}/issues/{n} --jq .id`. It has to be that numeric id: `gh issue view <n> --json id` returns the GraphQL node id, which this endpoint rejects. And it has to be sent with `-F` rather than `-f`, because `-f` sends the number as a string and the API answers `HTTP 422: Invalid property /issue_id: "5199031511" is not of type integer`.

### Stop

Call `CronList`, then call `CronDelete` once per job it returns — all of them, not only the eight this skill created. "Delete all your reminders" means the session ends with an empty schedule. Call `CronList` again afterwards to confirm it is empty, and report how many jobs were deleted.

`CronList` returning nothing is not a failure; say the schedule was already empty and stop.

## Notes

### Editing this file does not reach a running session

The body is read when the skill is invoked, so a change here needs `/autopilot stop` and `/autopilot start` before it takes effect. A session that solved the issue which changed this file and then carried on is still working from the scope it started with, and will report that it has run out of issues rather than that it is reading the wrong set.
### How the reminders fire

A job fires only while the session is idle, never mid-turn, because a turn cannot be preempted. So this skill cannot correct drift inside a task; what it can do is restart a loop that has stalled, which is the failure it is there to catch. It is also why `:07` earns its slot — a session waiting on a run is idle, so that is exactly when a reminder lands, and the answer to it is to keep waiting.

Fire times drift by up to a tenth of the period, a minute here, and the offsets from `:03` on are a minute apart, so `:03` can arrive in the same minute as `:04`. A pair landing together is the tool working as documented, not a job created wrong, and not worth re-spacing the table over.

Both together are why `start` does the work rather than only arming the jobs: the first reminder is up to eleven minutes out, so a session that created the eight and then stopped sits silent for a whole period and looks broken.

### The :05 and :09 reminders are written down nowhere else

`:05` is the one rule `CLAUDE.md` does not carry, and the table above is the only copy of it: delete the reminder and the rule leaves the repository with it. `:09` carries the two-section issue form as well as the six-section one, because a reminder that names only one case is read as though that case were the whole rule, and most of the open queue here is workflow and config work. Neither prompt is longer than it needs to be.

### The standing rules live in CLAUDE.md

`CLAUDE.md` at the root of the repository carries verification in CI, committing straight to `main`, the test tiers and the two issue forms, and is read at the start of every turn. This file does not restate any of it — a rule kept in two places drifts with nothing to signal it. The reminders exist for the part `CLAUDE.md` cannot reach: a rule read at the start of a turn is not read again forty minutes into one, and a session that has stopped is not reading anything at all.

