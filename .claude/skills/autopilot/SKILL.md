---
name: autopilot
description: Start or stop the standing reminders that keep an autonomous issue-solving session on the rails. Use when the user says "start autopilot", "go autonomous on issues above N", "stop autopilot", or asks to clear the reminders. Takes "start <issue-number>" or "stop".
---

# Autopilot

Eight recurring reminders, one per standing rule, that fire back into this session while it works through the open issues on `10U-Labs/10ulabs.com` on its own. Each rule gets its own reminder so that no rule can be quietly dropped from a merged block of text, and the fire times are staggered across the ten-minute period so they arrive one at a time rather than as a wall.

The argument is the sub-command: `start <issue-number>` or `stop`.

`CronCreate`, `CronList` and `CronDelete` are deferred tools: the session is told their names but not their schemas, so a call made before the schema is fetched fails with `InputValidationError` and creates nothing. Fetch them first with `ToolSearch`, query `select:CronCreate,CronList,CronDelete`: `start` calls `CronCreate`, `stop` calls `CronList` and `CronDelete`.

## Start

The issue number is required — it is the `{X}` in the `:01` reminder, and it is the floor for this repository: every open issue above it here is in scope. An issue reached by following a dependency out of that set is in scope as well, whatever its number and whatever repository it lives in, because numbering in one repository says nothing about another: an issue numbered below the floor here can be numbered below it everywhere and still be the thing that has to be done first. `1e45d1f9` closed an issue in another repository for exactly that reason. If the user did not give an issue number, ask for it before creating anything.

Create eight jobs with `CronCreate`, exactly as listed below. Use `recurring: true` (the default). Substitute the issue number for `{X}` in the first prompt and leave the other seven verbatim. Each `cron` field is a distinct offset within the same ten-minute period, so the eight reminders never land together:

| Offset | Cron | Prompt |
| --- | --- | --- |
| :01 | `1,11,21,31,41,51 * * * *` | `REMINDER: Continue to solve open issues greater than issue {X} autonomously, unless you need human feedback about ANYTHING — not just about the next open issue.` |
| :03 | `3,13,23,33,43,53 * * * *` | `REMINDER: Issues must be solved through a single commit & push.` |
| :04 | `4,14,24,34,44,54 * * * *` | `REMINDER: Issues must be solved through a set of indivisible Claude tasks.` |
| :05 | `5,15,25,35,45,55 * * * *` | `REMINDER: Lead with what the thing is for. Every paragraph — in chat as much as in issues, commits and comments — opens with a plain sentence saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top, not in the seventh paragraph. Then cut the details that change nothing the reader would do.` |
| :06 | `6,16,26,36,46,56 * * * *` | `REMINDER: Ensure Claude tasks are indivisible.` |
| :07 | `7,17,27,37,47,57 * * * *` | `REMINDER: Do not do anything but wait while a workflow is running.` |
| :08 | `8,18,28,38,48,58 * * * *` | `REMINDER: An issue you file goes into the sequence before you go back to work. Add a blocked_by edge: the issue in hand is blocked by the new one if it cannot be finished without it, otherwise whichever issue in the set cannot be finished without it, otherwise the new issue is blocked by the tail of the sequence. Never leave a filed issue with no edge.` |
| :09 | `9,19,29,39,49,59 * * * *` | `REMINDER: When you come up against a new problem, file a GitHub issue. A problem in the program — src/, lib/python/, lib/terraform/, scripts/ — gets the sub-headers "Problem", "Why Unit Tests Did Not Catch It", "Why Integration Tests Did Not Catch It", "Why E2E Tests Did Not Catch It", "Which Unit, Integration, or E2E regression tests would prevent this from happening again?", and "Proposed Solution". A problem in a config, a map, a workflow file or the docs — etc/, .github/, docs/, products/ — gets "Problem" and "Proposed Solution" only, and owes no tests.` |

Then tell the user which issue number is in force, that eight reminders are running, and the two limits that come with them: the jobs live in this session only and are gone when it ends, and recurring jobs auto-expire after seven days.

Then start working, in the same turn that created the jobs. Read the open issues above `{X}` with `gh issue list`, then read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each of them; every entry names the repository its blocker lives in. Follow those entries, and the entries of the issues they reach, until nothing new comes back, and add every open issue found this way to the set. Then take the lowest-numbered issue in the set that no open issue blocks, preferring this repository when two are equally unblocked, and begin solving it under the standing rules the reminders carry — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it. Running this skill is starting the work; the eight jobs only keep it on the rails once it is going.

An issue filed during a run goes into the sequence before the session goes back to work. A `blocked_by` edge points from the issue that waits to the issue it waits on, and which issue gets the edge follows from three cases that between them cover everything. If the issue in hand cannot be finished until the new one is, the issue in hand gets the new one as a `blocked_by`, which puts the new issue immediately in front of it — and in front of the whole sequence when the issue in hand is its head. If some other issue in the set cannot be finished until the new one is, that issue gets the new one as a `blocked_by`. If neither is true, the new issue gets an edge to the tail of the sequence, the one open issue in the set that no other open issue is blocked by. There is no fourth case and nothing to choose between: an issue is either needed before something already in the sequence or it is not.

The tail is read rather than remembered, because this repository files issues in batches and the tail moves with them — #518 through #522 were all filed within five seconds of each other. `gh issue view <n>` prints a `blocked-by` and a `blocking` line, which is enough to place a new issue without walking the API twice: #522 shows `blocking: #517, #513, #519` and an empty `blocked-by`, so it is a head of the set rather than its tail.

A filed issue is never left without an edge. An issue with no edge in this repository is worked last whatever it is about, because it always carries the highest number and the tie-break above takes the lowest; an issue with no edge in another repository is not reached at all, because the traversal gets there only by following an edge into it.

Add the edge with `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F issue_id=<id>`, where `{number}` is the issue that waits and `<id>` is the numeric id of the blocker, read from `gh api repos/{owner}/{repo}/issues/{n} --jq .id`. It has to be that numeric id: `gh issue view <n> --json id` returns the GraphQL node id, which this endpoint rejects. And it has to be sent with `-F` rather than `-f`, because `-f` sends the number as a string and the API answers `HTTP 422: Invalid property /issue_id: "5199031511" is not of type integer`.

## Stop

Call `CronList`, then call `CronDelete` once per job it returns — all of them, not only the eight this skill created. "Delete all your reminders" means the session ends with an empty schedule. Call `CronList` again afterwards to confirm it is empty, and report how many jobs were deleted.

`CronList` returning nothing is not a failure; say the schedule was already empty and stop.

## Notes

The reminders are the rulebook while a session runs here, because this repository has no `CLAUDE.md` for it to read at the start of a turn. What it does have is `docs/tenets/tests/`, which states what each test tier is for. Those are tenets — they name no directory or tool and they do not say how to work through a queue of issues, which is the gap these eight fill. A rule that is in neither place is not in force, so a rule worth keeping goes into a reminder here or into `docs/tenets/`, not into a chat message.

Verification happens in CI. Workflows here are path-filtered, so one push starts several and the change is done when each of them is green rather than when the first one is; `workflowctl.yml` runs on every push and carries the tree-wide pylint, mypy and jscpd passes. Read the run by the full forty-character hash from `git rev-parse HEAD`, since `gh run list --commit` answers an empty list for a short hash and that is indistinguishable from a run that has not started.

Work goes straight to `main`. The history is direct commits — `31f0066f` and everything above it — and the merge commits below `33031228` are the older pull-request habit, not the current one. There is no review buffer, so the tests land in the same commit as the code they cover, and a push rejected by CI is answered with a follow-up commit rather than an amend and a force-push.

A commit closes its issue in the message: `Closes #490` in `31f0066f`, and the qualified `Fixes <owner>/<repo>#<n>` that `1e45d1f9` carries when the issue lives in another repository. That line is what makes the queue drain — an issue solved by a push that does not carry it stays open and gets picked up again on the next traversal.

The `:03` and `:06` reminders pull against each other on purpose. One commit per issue means the work is not spread across pushes; indivisible tasks means it is planned as steps that each finish or do not. An issue that cannot be done in one commit is two issues, and filing the second is what the `:08` and `:09` reminders are for.

Starting autopilot begins the work in the same turn. Arming the reminders and doing the work look like separate things, and separating them produces a session sitting idle after `/autopilot start 522`: a cron job fires only when the session is idle and the first one is up to ten minutes out, so the skill looks like it has not worked at all. A start at eight minutes past gets going in a minute and looks fine; a start at ten minutes past sits silent for the whole period, and that is the same skill on the same rules.

The three cron tools are deferred, which is why `Start` and `Stop` both open by fetching their schemas. A deferred tool is listed to the session by name only, so the first `CronCreate` call is rejected as invalid input and no job is created — a failure that reads like the tool is missing rather than like a step was skipped.

Cron jobs fire only while the session is idle, never mid-turn, because a turn cannot be preempted. That limit is the reason this skill does not try to correct drift in the middle of a task: what it can do is restart a loop that has stalled, which is the failure it is there to catch. It is also why the `:07` reminder is worth its slot — a session waiting on a run is idle, so that is exactly when a reminder lands, and the answer to it is to keep waiting.

The `:05` reminder is the writing already in the log, said in advance. `31f0066f` opens by saying an AMI build was launching for files the runner never sees and that it cost twenty minutes a time, and only then names `etc/workflow_dependencies.json` and the glob it narrowed. A reminder that named only structure would be read as though structure were the whole of it, which is why this one names the order and the cut as well, and why it says "every paragraph" rather than "every issue".

The `:09` reminder carries the two-section form as well as the six, because a reminder that names only one case is read as though the case were the whole rule. Most of the open queue here is workflow and config work — #518 through #522 are all triggers in `.github/workflows/` — and a defect in a `paths` list arriving beside a standing instruction to name the regression tests that would prevent it makes the session argue at length that none are owed. The split is by directory so there is nothing to weigh: `src/`, `lib/python/`, `lib/terraform/` and `scripts/` owe tests, `etc/`, `.github/`, `docs/` and `products/` do not.

Tests that are owed go in the tier the change touches. Every subsystem under `test/` is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when there is a test to put in it. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call.

The three placement cases in `## Start` are settled by fact rather than by taste, so a session filing an issue has nothing to weigh and nothing to ask about. Asking it to append, prepend or interpose as it judges best hands the decision to whoever is least able to make it: the session filing the issue knows what the issue is, which is exactly what the three cases read, and does not know what the sequence is for. The rule needs a reminder of its own because it is not read at invocation and then held.

The skill body is read when the skill is invoked, so editing this file does not reach a session already running under it. Whoever lands a change here has to `/autopilot stop` and `/autopilot start` again before it takes effect: a session that solved the issue which changed this file and then carried on is still working from the scope it was started with, and it will report that it has run out of issues rather than that it is reading the wrong set of them.

A reminder in this file is named by the minute it fires — the `:01` reminder, the `:09` reminder — and a line in it is written out in full, as "line 22". The rest of the repository writes `path/to/file.yml:115` for a line and then a bare `:120` for another line in the same file, the way #522 does, and that shorthand collides here: line 22 is the `:01` reminder, so "the reminder at `:22`" sends a reader looking for a reminder that fires at minute 22, and there is none.
