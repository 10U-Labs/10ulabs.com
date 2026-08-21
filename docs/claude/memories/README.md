# Notes for Claude sessions in 10ulabs.com

`CLAUDE.md` at the repository root carries the standing conventions in short form and is read at the start of every session. These files carry the longer versions: the reasoning, the incidents that produced each rule, and the details needed occasionally rather than constantly. One note per topic, so a session can read the one rule it needs.

A convention learned in a session belongs here — a paragraph in `CLAUDE.md` and a topic file in this directory, linked from both indexes. Keep in the session tool's local memory only what is true of one machine alone; a rule kept in both places drifts with nothing to signal it, which is why the local copy of the CI rule was deleted when [verification-in-ci-only](verification-in-ci-only.md) was written.

## Working practice

- [verification-in-ci-only](verification-in-ci-only.md) — nothing runs locally; push and read the run, and read the code here instead
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, and says nothing about why
- [commit-straight-to-main](commit-straight-to-main.md) — direct commits, no branches and no pull requests, one commit per issue with its closing line
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a failed run is answered with a follow-up commit, never an amended force-push
- [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md) — no column limit on `.md` files or on issue bodies

## Issues

- [how-issues-are-written](how-issues-are-written.md) — six fixed sections for the program, two for everything else, plain English, no test owed for a config or a workflow file
- [an-issue-states-one-solution](an-issue-states-one-solution.md) — a `Proposed Solution` names one change; a fork is asked about before the issue is filed, never published as an either

## Tests

- [tdd-workflow](tdd-workflow.md) — the test is written before the code, in the same commit
- [read-test-tenets-first](read-test-tenets-first.md) — read `docs/tenets/tests/` before implementing, and cover every tier the change touches
- [tenets-are-generic](tenets-are-generic.md) — the four tier files name no tool, language or directory and the repository follows them; `OVERVIEW.md` describes this suite and loses to the tree
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` for a subsystem that deploys, and nothing of the kind under `test/lib/`

## The one rule with no note here

Leading with what a thing is for — every paragraph opening with a plain sentence before any file, function or line is named — is in force and is written down in one place only, the `:05` reminder of `.claude/skills/autopilot/SKILL.md`. Delete that reminder and the rule leaves the repository. It belongs in a note here.
