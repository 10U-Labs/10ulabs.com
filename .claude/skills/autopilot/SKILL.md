---
name: autopilot
description: Start or stop the standing reminders that keep an autonomous issue-solving session on the rails. Use when the user says "start autopilot", "go autonomous on the open issues", "stop autopilot", or asks to clear the reminders. Takes "start" or "stop".
---

# Autopilot

## Table of Contents

- [Overview](#overview)
- [Sub-Commands](#sub-commands)
  - [Start](#start)
    - [Create the reminders](#create-the-reminders)
    - [Start working](#start-working)
    - [Place a filed issue](#place-a-filed-issue)
  - [Stop](#stop)

## Overview

Seven recurring reminders, one per standing rule, that fire back into this session while it works through the open issues on `10U-Labs/10ulabs.com` on its own. One reminder per rule, so no rule can be quietly dropped from a merged block of text; staggered across a ten-minute period so they arrive spread out rather than as a wall.

The argument is the sub-command, `start` or `stop`. Neither takes anything else — `start` reads its scope out of the repository. If the user names an issue number anyway, they are asking to start rather than to narrow; say the whole open set is in scope and start.

`CronCreate`, `CronList` and `CronDelete` are deferred tools: the session is told their names but not their schemas, so a call made before the schema is fetched fails with `InputValidationError` and creates nothing. Fetch them first with `ToolSearch`, query `select:CronCreate,CronList,CronDelete`.

## Sub-Commands

### Start

#### Create the reminders

Create seven jobs with `CronCreate`, exactly as listed. Use `recurring: true` (the default), and take the prompts verbatim; none of them has anything to substitute. Each `cron` field is a distinct offset within the same ten-minute period. Two reminders can still arrive in the same minute, because a recurring job fires up to a tenth of its period late; that is documented drift, not a job created wrong, and the table is not to be re-spaced over it.

| Offset | Cron | Prompt |
| --- | --- | --- |
| :01 | `1,11,21,31,41,51 * * * *` | `REMINDER: Continue to solve the open issues autonomously, unless you need human feedback about ANYTHING — not just about the next open issue.` |
| :03 | `3,13,23,33,43,53 * * * *` | `REMINDER: Issues must be solved through a single commit & push.` |
| :04 | `4,14,24,34,44,54 * * * *` | `REMINDER: Issues must be solved through a set of indivisible tasks held in Claude Code's native structured task list — TaskCreate one entry per step before starting, TaskUpdate each to in_progress and then completed as it lands. A breakdown kept only in your head is not a breakdown.` |
| :06 | `6,16,26,36,46,56 * * * *` | `REMINDER: Ensure the entries in Claude Code's native structured task list are indivisible. Read the list back with TaskList; split any entry that cannot be finished in one step.` |
| :07 | `7,17,27,37,47,57 * * * *` | `REMINDER: Do not do anything but wait while a workflow is running.` |
| :08 | `8,18,28,38,48,58 * * * *` | `REMINDER: An issue you file is placed before you go back to work, and a blocked_by edge is written only where the block is real. Add one when the issue in hand cannot be finished until the new one is, or when some other open issue cannot. Where nothing waits on it, file it with no edge and move on: an ordering is not a dependency, and an edge written to give an issue a place in the queue is a false statement about the work.` |
| :09 | `9,19,29,39,49,59 * * * *` | `REMINDER: When you come up against a new problem, file a GitHub issue. A problem in the program — src/, lib/python/, lib/terraform/, scripts/ — gets the sub-headers "Problem", "Why Unit Tests Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?", "Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?", and "Proposed Solution". A problem in a workflow file or the docs — .github/, docs/ — gets "Problem" and "Proposed Solution" only, and owes no tests.` |

Then tell the user that seven reminders are running, how many open issues are in scope, and the two limits that come with them: the jobs live in this session only and are gone when it ends, and recurring jobs auto-expire after seven days.

#### Start working

Start in the same turn that created the jobs. Running this skill is starting the work; the seven jobs only keep it on the rails once it is going.

Read the open issues with `gh issue list`, then read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each of them; every entry names the repository its blocker lives in. Follow those entries, and the entries of the issues they reach, until nothing new comes back, and add every open issue found this way to the set. Then take the lowest-numbered issue in the set that no open issue blocks, preferring this repository when two are equally unblocked, and solve it under the standing rules the reminders carry — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it.

Most of the set is unblocked, so most of the time that pick is the lowest open number, and that is the intended shape rather than a sign the edges are missing. An issue in another repository enters the set only by an edge, and edges are written only where a block is real, so work that belongs elsewhere is filed here and says so in its `Proposed Solution` — `#586` is filed on this repository and directs a change at `10U-Labs/assert-python-definition-is-used`.

#### Place a filed issue

An issue filed during a run is placed before the session goes back to work. A `blocked_by` edge says that one piece of work cannot be finished until another is, so it is written where that is true and left unwritten where it is not. Two cases put an edge on:

- The issue in hand cannot be finished until the new one is: the issue in hand gets the new one as a `blocked_by`, which puts the new issue in front of it.
- Some other open issue cannot be finished until the new one is: that issue gets the new one as a `blocked_by`.

Where neither holds, the new issue is filed with no edge at all, and that is a finished placement rather than a missing one. It is worked by number like every other issue nothing blocks. Do not reach for an edge onto the tail of the queue to give it a position: an ordering is not a dependency, and an edge written to express one is a false statement that the next reader has to take at face value and work around.

Decide it by reading rather than by feel. Ask whether the waiting issue's own `Proposed Solution` can land green with the other one not done. A solution that already carries the contingency — "if it has not gone with the other issue, delete it here and say so in the commit" — has answered the question against itself: it is finishable in either order and takes no edge. A solution that would land red, or that names a job, a flag or a file the other issue creates, is blocked and takes one.

`gh issue view <n>` prints a `blocked-by` and a `blocking` line, which is enough to read the edges on one issue without walking the API.

Add the edge with `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F issue_id=<id>`, where `{number}` is the issue that waits and `<id>` is the numeric id of the blocker, read from `gh api repos/{owner}/{repo}/issues/{n} --jq .id`. It has to be that numeric id: `gh issue view <n> --json id` returns the GraphQL node id, which this endpoint rejects. And it has to be sent with `-F` rather than `-f`, because `-f` sends the number as a string and the API answers `HTTP 422: Invalid property /issue_id: "5199031511" is not of type integer`.

Remove an edge that should not have been written with `gh api -X DELETE repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by/<id>`, taking the blocker's numeric id in the path. It answers with the whole issue rather than an empty body, so confirm the removal by reading the `blocked_by` list again rather than by the exit status.

### Stop

Call `CronList`, then call `CronDelete` once per job it returns — all of them, not only the seven this skill created. "Delete all your reminders" means the session ends with an empty schedule. Call `CronList` again afterwards to confirm it is empty, and report how many jobs were deleted.

`CronList` returning nothing is not a failure; say the schedule was already empty and stop.
