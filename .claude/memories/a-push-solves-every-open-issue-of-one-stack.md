---
name: a-push-solves-every-open-issue-of-one-stack
description: "A batch is every open issue whose fix lands in one workflow's stack, bounded by the stack and never by a count; its tests and its fix go in one commit; a change under a path several workflows fire on goes alone"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:37:56.562Z
---

# A push solves every open issue of one stack

A batch is every open issue that shares one matter, and the matter bounds it, never a count. Two issues share a matter when their fixes land in the same workflow's stack: the paths only one workflow under `.github/workflows/` fires on.

| Workflow | Stack |
| --- | --- |
| `bootstrap.yml` | `src/bootstrap/`, `test/bootstrap/` |
| `www_common.yml` | `src/www/common/`, `test/www/common/` |
| `www_home.yml` | `src/www/paths/home/`, `test/www/paths/home/` |
| `www_rack_designer.yml` | `src/www/paths/rack_designer/`, `test/www/paths/rack_designer/` |
| `scripts.yml` | `scripts/`, `test/scripts/` |

**Why:**

- **Traceable red runs.** A batch inside one stack fires one workflow, so a red run points at files the batch touched, however many issues it holds. A batch spanning stacks turns every failing job into a search through unrelated changes. What makes a batch too big to trace is the number of stacks it mixes, not the number of issues it holds, so a count would cap the wrong thing.
- **Waiting.** Each push waits out its runs, and nothing else happens while they run. A batch of n issues shares that wait n ways.
- **Shared reading.** Issues of one stack are fixed in the same Terraform, the same handlers and the same tests, so the reading done for the first serves the rest.

**How to apply:**

1. **Seed.** Take the issue the loop's command names first.
2. **Gather.** Add every open issue of the seed's stack. Leave out every issue labelled `needs decision`, and bring each issue up to date before starting it. When an issue's stack cannot be told without investigating it, take it in; if its fix turns out to land elsewhere, it leaves the batch and seeds a later one.
3. **Solve.** Solve the issues one after another in the working tree, each one's tests written before its source ([[tests-are-written-before-source]]), and commit nothing until the last is done. The tests are never pushed as a commit of their own ahead of the fix. As each issue is finished, write its paragraph of the commit message into the scratchpad, so nothing depends on the context outlasting the batch. An issue that turns out to need a person's decision is labelled for one, and its edits and tests come out of the tree before the commit.
4. **Commit.** Commit once, to main ([[commits-go-straight-to-main]]). The subject names the stack and what the batch does to it rather than joining every issue's subject; the body gives each issue its own paragraph; the message ends with one `Closes #N` line per issue.
5. **Push and read the run.** CI is the verification ([[do-not-run-test-suites-locally]]). When it goes red, trace each failing job to the issue whose change it names and fix forward.

Some changes go in a push of their own and are never batched:

- A change under a path several workflows fire on: `lib/python/`, `lib/terraform/`, `test/conftest.py`, `test/lib/`, `test/www/conftest.py`, `test/www/paths/conftest.py`, `.github/actions/` or `.github/workflows/`. Such a change alters what verifies every stack or what every stack runs through, so its fallout would hide the batch's own results.
- The fix for a red run.

A change under `.claude/`, such as a memory or a skill, can join any batch, since only the Markdown lint checks it.
