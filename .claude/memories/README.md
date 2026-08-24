# Notes for Claude sessions in 10ulabs.com

## Table of Contents

- [What these notes are](#what-these-notes-are)
- [Working practice](#working-practice)
- [Issues](#issues)
- [Tests](#tests)

## What these notes are

`CLAUDE.md` at the repository root carries the standing conventions in short form and is read at the start of every session. These files carry the longer versions: the reasoning, the incidents that produced each rule, and the details needed occasionally rather than constantly. One note per topic, so a session can read the one rule it needs.

A convention learned in a session belongs here — a paragraph in `CLAUDE.md` and a topic file in this directory, linked from both indexes and written in the shape the notes around it use. That shape is a top-level heading, a table of contents, and `##` sections named for the questions the note answers, so a session can jump to the one rule it needs instead of reading from the top. Keep in the session tool's own memory directory under the home directory only what is true of one machine alone; a rule kept in both places drifts with nothing to signal it, which is why the local copy of the CI rule was deleted when [verification-in-ci-only](verification-in-ci-only.md) was written.

## Working practice

- [verification-in-ci-only](verification-in-ci-only.md) — nothing runs locally; push and read the run, and read the code here instead
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, and says nothing about why
- [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md) — linter and type checker, over source and over tests, four jobs with the same names in every workflow
- [commit-straight-to-main](commit-straight-to-main.md) — direct commits, no branches and no pull requests, one commit per issue with its closing line
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a failed run is answered with a follow-up commit, never an amended force-push
- [prose-leads-with-the-concept](prose-leads-with-the-concept.md) — lead with what the thing is for, write in concepts rather than identifiers, use the exact technical term where no plain word is as precise, one idea to a sentence
- [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md) — no column limit on `.md` files, on issue bodies or on commit message bodies
- [never-write-the-skip-ci-brackets-in-prose](never-write-the-skip-ci-brackets-in-prose.md) — a commit message that names the bracketed directive starts no workflow, so prose about it drops the brackets

## Issues

- [how-issues-are-written](how-issues-are-written.md) — six fixed sections for the program, two for everything else, identifiers only in the solution, no test owed for a config or a workflow file
- [an-issue-states-one-solution](an-issue-states-one-solution.md) — a `Proposed Solution` names one change; a fork is asked about before the issue is filed, never published as an either
- [file-what-the-sweep-turns-up](file-what-the-sweep-turns-up.md) — a defect found while working on something else is filed in the same turn, not named in a reply and left for the user to ask for
- [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) — a `blocked_by` edge is written only where the work cannot be finished without the other issue; an issue nothing waits on is filed with no edge

## Tests

- [tdd-workflow](tdd-workflow.md) — the test is written before the code, in the same commit
- [read-test-tenets-first](read-test-tenets-first.md) — read `docs/tenets/tests/` before implementing, and cover every tier the change touches
- [tenets-are-generic](tenets-are-generic.md) — the four tier files name no tool, language or directory and the repository follows them; `OVERVIEW.md` describes this suite and loses to the tree
- [a-conftest-is-emptied-never-deleted](a-conftest-is-emptied-never-deleted.md) — a `conftest.py` whose last fixture goes is emptied to zero bytes and left in place, so the level stays visible to whoever writes the next one
- [test-code-is-placed-by-how-many-suites-use-it](test-code-is-placed-by-how-many-suites-use-it.md) — a fixture goes at the highest level that applies, and a helper is shared by its number of callers rather than by its name
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` for a subsystem that deploys, and nothing of the kind under `test/lib/`
