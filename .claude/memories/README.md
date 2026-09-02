# Notes for Claude sessions in 10ulabs.com

## Table of Contents

- [What these notes are](#what-these-notes-are)
- [Working practice](#working-practice)
- [Comments](#comments)
- [Issues](#issues)
- [Tests](#tests)

## What these notes are

`CLAUDE.md` at the repository root carries the standing conventions in short form and is read at the start of every session. These files carry the longer versions: the reasoning, the incidents that produced each rule, and the details needed occasionally rather than constantly. One note per topic, so a session can read the one rule it needs.

A convention learned in a session belongs here — a paragraph in `CLAUDE.md` and a topic file in this directory, linked from both indexes and written in the shape the notes around it use. That shape is a top-level heading, a table of contents, and `##` sections named for the questions the note answers, so a session can jump to the one rule it needs instead of reading from the top. Keep in the session tool's own memory directory under the home directory only what is true of one machine alone; a rule kept in both places drifts with nothing to signal it, which is why the local copy of the CI rule was deleted when [verification-in-ci-only](verification-in-ci-only.md) was written.

## Working practice

- [verification-in-ci-only](verification-in-ci-only.md) — nothing runs locally; push and read the run, and read the code here instead
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, and says nothing about why
- [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md) — linter and type checker, over source and over tests, four jobs with the same names in every workflow
- [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md) — the four passes name the `lib/python/` packages the workflow runs and the suites covering them, in every workflow that runs them
- [a-workflow-runs-the-suites-of-the-packages-it-executes](a-workflow-runs-the-suites-of-the-packages-it-executes.md) — the running half of the same rule: a `test-*` job per `lib/python/` package the workflow executes, a package reached only through another travelling with it
- [an-eslint-config-is-read-from-wherever-eslint-was-started](an-eslint-config-is-read-from-wherever-eslint-was-started.md) — a glob in a flat eslint config is anchored at the working directory when the file is passed with `--config` and at the file itself when eslint found it
- [every-tool-is-installed-at-latest](every-tool-is-installed-at-latest.md) — every package a workflow installs is named with no version specifier on purpose, so a checker's new release is a finding here the day it ships
- [a-mypy-flag-reaches-every-module-it-follows](a-mypy-flag-reaches-every-module-it-follows.md) — a mypy command's argument list says where the reading starts, not where it stops; the flags apply to the whole import closure
- [an-annotation-can-turn-a-near-duplicate-into-a-clone](an-annotation-can-turn-a-near-duplicate-into-a-clone.md) — `jscpd` counts tokens against a floor of fifty, so lengthening every signature in a file crosses it for pairs that had sat under it
- [commit-straight-to-main](commit-straight-to-main.md) — direct commits, no branches and no pull requests, one commit per issue with its closing line
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a failed run is answered with a follow-up commit, never an amended force-push
- [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md) — no column limit on `.md` files, on issue bodies or on commit message bodies
- [never-write-the-skip-ci-brackets-in-prose](never-write-the-skip-ci-brackets-in-prose.md) — a commit message that names the bracketed directive starts no workflow, so prose about it drops the brackets

## Comments

- [nothing-carries-a-comment-or-a-docstring](nothing-carries-a-comment-or-a-docstring.md) — no `#` and no docstring in anything a job reads; the reasoning moves to the commit message and the issue, which are dated

## Issues

- [how-issues-are-written](how-issues-are-written.md) — seven fixed sections for the program, two for everything else, no test and no static analysis question owed for a config or a workflow file
- [an-issue-states-one-solution](an-issue-states-one-solution.md) — a `Proposed Solution` names one change; a fork is asked about before the issue is filed, never published as an either
- [solve-what-the-sweep-turns-up](solve-what-the-sweep-turns-up.md) — a defect found while working on something else is fixed in the session that found it; an issue is filed only where the fix needs the user
- [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) — a `blocked_by` edge is written only where the work cannot be finished without the other issue; an issue nothing waits on is filed with no edge
- [enumerate-a-directory-from-git](enumerate-a-directory-from-git.md) — a body that counts or names what a directory holds reads `git ls-files`, because `ls` shows ignored artifacts git will not report and `git status` stays clean over them

## Tests

- [tdd-workflow](tdd-workflow.md) — the test is written before the code, in the same commit
- [a-test-does-not-restate-the-source](a-test-does-not-restate-the-source.md) — a test asserts a property the program must have, never a copy of what the source says, because it is written before the source exists
- [a-test-says-what-it-checked](a-test-says-what-it-checked.md) — one assertion per pytest and it has to be able to fail; `assert f(...) is None` over a `-> None` function is refused by mypy and its deletion by the assert job
- [read-test-tenets-first](read-test-tenets-first.md) — read `docs/tenets/tests/` before implementing, and cover every tier the change touches
- [tenets-are-generic](tenets-are-generic.md) — the four tier files name no tool, language or directory and the repository follows them
- [a-conftest-is-emptied-never-deleted](a-conftest-is-emptied-never-deleted.md) — a `conftest.py` whose last fixture goes is emptied to zero bytes and left in place, so the level stays visible to whoever writes the next one
- [test-code-is-placed-by-how-many-suites-use-it](test-code-is-placed-by-how-many-suites-use-it.md) — a fixture goes at the highest level that applies, and a helper is shared by its number of callers rather than by its name
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` for a subsystem that deploys, and nothing of the kind under `test/lib/`
