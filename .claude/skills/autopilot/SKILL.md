---
name: autopilot
description: Start, restart or stop the autopilot reminders. Use when the user says "start autopilot", "go autonomous on the open issues", "restart autopilot", "stop autopilot" or "reminders only", or asks to clear the reminders. Takes "start", "start bylabel <label>", "start reminders-only", the same three after "restart", or "stop"; every form but "reminders-only" and "stop" also takes `--skip-label <label>`, repeatable.
---

# Autopilot

Fetch `CronCreate`, `CronList`, `CronDelete`, `TaskCreate` and `TaskUpdate` with `ToolSearch` first.

## Standing reminders

Every form.

| Cron | Prompt |
| --- | --- |
| `0,15,30,45 * * * *` | `REMINDER: Work through a set of indivisible tasks, written down with TaskCreate before the work starts and marked with TaskUpdate as each one starts and finishes.` |
| `3,18,33,48 * * * *` | `REMINDER: Let every push carry exactly one commit, and let that commit hold a whole body of work: a matter solved end to end or carried out in full, or a batch of every open issue of one matter (one workflow's stack, such as src/bootstrap/ with test/bootstrap/), bounded by the matter and never by a count.` |
| `5,20,35,50 * * * *` | `REMINDER: Before working on an issue, ensure the issue is up to date. If it is outdated, rewrite its title and body as necessary and ensure its labels are correct. Ensure too that it documents a single indivisible problem; if it documents more than one, split it into one issue per problem, reusing the issue itself as one of those splits.` |
| `6,21,36,51 * * * *` | `REMINDER: Keep the task list itself current, not only the marks on it: a task that arises is added the moment it does, a task that turns out unneeded is removed, and a task whose shape changed is rewritten, so that the list always says what is left to do.` |
| `7,22,37,52 * * * *` | `REMINDER: While any CI run for a pushed commit is in progress, only wait: no diagnosis, edits or commits.` |
| `8,23,38,53 * * * *` | `REMINDER: File what you find as issues, each documenting one indivisible problem. Solve one now only if the work in hand cannot move forward without it; otherwise move on.` |
| `9,24,39,54 * * * *` | `REMINDER: Ensure every task on the list is indivisible, whether it was written with TaskCreate or rewritten with TaskUpdate: read each subject as written and count the actions it names; a subject naming more than one action is divisible, whatever single purpose those actions serve, and is split into one task per action.` |
| `10,25,40,55 * * * *` | `REMINDER: Prune completed tasks off the Claude Code structured task list: set every task marked completed to the status deleted with TaskUpdate, so that the list holds only the tasks still open.` |
| `12,27,42,57 * * * *` | `REMINDER: An issue you file is placed before you go back to work, and a blocked_by edge is written only where the block is real. Add one when the issue in hand cannot be finished until the new one is, or when some other open issue cannot. Where nothing waits on it, file it with no edge and move on: an ordering is not a dependency, and an edge written to give an issue a place in the queue is a false statement about the work.` |
| `13,28,43,58 * * * *` | `REMINDER: When you come up against a new problem, file a GitHub issue. A problem in the program — src/, lib/python/, lib/terraform/, scripts/ — gets the sub-headers "Problem", "Why Unit Tests Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?", "Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?", and "Proposed Solution". A problem in a workflow file or the docs — .github/, docs/ — gets "Problem" and "Proposed Solution" only, and owes no tests.` |

## Loop reminders

Every form but `reminders-only`.

On `1,16,31,46 * * * *`, for `start`:

```text
REMINDER: Run gh issue list --state open --search '-label:"needs decision"' --limit 1000 --json number,title,labels --jq 'sort_by(.number) | map({number, title, labels: [.labels[].name]})' for the open issues no decision holds back, lowest number first; take the first that no open issue blocks, together with every other issue in the list of its matter (fixed in the same workflow's stack), as one batch, and run the same command again when they close. An issue labelled 'needs decision' is left to a person.
```

For `start bylabel <label>`:

```text
REMINDER: Run gh issue list --state open --label '{L}' --search '-label:"needs decision"' --limit 1000 --json number,title,labels --jq 'sort_by(.number) | map({number, title, labels: [.labels[].name]})' for the open issues labelled '{L}', lowest number first; take the first that no open issue blocks, together with every other issue in the list of its matter (fixed in the same workflow's stack), as one batch, and run the same command again when they close. The open issues without the label '{L}' are not this loop's work, and an issue labelled 'needs decision' is left to a person.
```

| Cron | Prompt |
| --- | --- |
| `4,19,34,49 * * * *` | `REMINDER: Continue autonomously, unless you need human feedback about ANYTHING — not just about what to take next. When you do, rewrite the issue's title if necessary, rewrite the issue's body, label the issue 'needs decision', and move on to the next issue.` |
| `11,26,41,56 * * * *` | `REMINDER: Before labeling an issue with 'needs decision', assess the issue against the rulebook in .claude/memories/ and the code to determine whether it truly needs a decision.` |

## Start and restart

Each `--skip-label <label>` adds `-label:"<label>"` to the loop command's `--search` and appends `An issue labelled '<label>' is left to a person, whatever else it carries.` to its reminder.

1. Unless `reminders-only`, run the loop command once; if it names no issue, schedule the standing reminders only.
2. Call `CronList`. On `start`, `CronDelete` each job on one of the form's slots whose prompt differs from that slot's. On `restart`, `CronDelete` every job that is not one of the form's reminders, keeping one per slot.
3. `CronCreate` with `recurring: true` each of the form's reminders not already scheduled, the label substituted for `{L}`.
4. Unless `reminders-only`, widen the set per [Blocked issues](#blocked-issues), then solve the batch the first unblocked issue seeds, per `.claude/memories/a-push-solves-every-open-issue-of-one-stack.md`. When nothing is left, say which label or issue holds back each open issue and stop.

## Blocked issues

Read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each issue the loop command names; every entry names the repository its blocker lives in. Follow those entries, and the entries of the issues they reach, until nothing new comes back, and add every open issue found this way to the set. Take the lowest-numbered issue in the set that no open issue blocks, preferring this repository when two are equally unblocked, and solve it — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it.

Most of the set is unblocked, so most of the time that pick is the lowest open number, and that is the intended shape rather than a sign the edges are missing. Work that belongs in another repository is filed in that repository, under its own numbering and its own CI — `10U-Labs/assert-python-definition-is-used#6` is a defect in that tool, filed and closed there. What is filed here is this repository's own share of the work, which is a separate issue: `#586` is the job of adopting the mode `#6` added. An issue elsewhere enters the set only by an edge, and edges are written only where a block is real, so an issue nothing here waits on is worked in the repository it was filed in.

## Place a filed issue

An issue filed during a run is placed before the session goes back to work. A `blocked_by` edge says that one piece of work cannot be finished until another is, so it is written where that is true and left unwritten where it is not. Two cases put an edge on:

- The issue in hand cannot be finished until the new one is: the issue in hand gets the new one as a `blocked_by`, which puts the new issue in front of it.
- Some other open issue cannot be finished until the new one is: that issue gets the new one as a `blocked_by`.

Where neither holds, the new issue is filed with no edge at all, and that is a finished placement rather than a missing one. It is worked by number like every other issue nothing blocks. Do not reach for an edge onto the tail of the queue to give it a position: an ordering is not a dependency, and an edge written to express one is a false statement that the next reader has to take at face value and work around.

Decide it by reading rather than by feel. Ask whether the waiting issue's own `Proposed Solution` can land green with the other one not done. A solution that already carries the contingency — "if it has not gone with the other issue, delete it here and say so in the commit" — has answered the question against itself: it is finishable in either order and takes no edge. A solution that would land red, or that names a job, a flag or a file the other issue creates, is blocked and takes one.

`gh issue view <n>` prints a `blocked-by` and a `blocking` line, which is enough to read the edges on one issue without walking the API.

Add the edge with `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F issue_id=<id>`, where `{number}` is the issue that waits and `<id>` is the numeric id of the blocker, read from `gh api repos/{owner}/{repo}/issues/{n} --jq .id`. It has to be that numeric id: `gh issue view <n> --json id` returns the GraphQL node id, which this endpoint rejects. And it has to be sent with `-F` rather than `-f`, because `-f` sends the number as a string and the API answers `HTTP 422: Invalid property /issue_id: "5199031511" is not of type integer`.

Remove an edge that should not have been written with `gh api -X DELETE repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by/<id>`, taking the blocker's numeric id in the path. It answers with the whole issue rather than an empty body, so confirm the removal by reading the `blocked_by` list again rather than by the exit status.

## Stop

`CronDelete` every job `CronList` returns.
