# Memories

- [Commits go straight to main](commits-go-straight-to-main.md) — no branches, no PRs; CI only runs on main.
- [Don't verify locally](do-not-run-test-suites-locally.md) — push and let CI run the suites; local runs waste tokens.
- [Memories live in .claude/memories](memories-live-in-dot-claude-memories.md) — autoMemoryDirectory overrides the user-scoped default path.
- [Lint jobs take whole roots](lint-jobs-take-whole-roots.md) — src/ lib/, scripts/ lib/, test/ lib/ across all six jobs; never path lists.
- [Tests are written before source](tests-are-written-before-source.md) — TDD; a test may name a file that does not exist yet, but read it via a fixture, never at module level.
- [Fixture liveness needs a collection](fixture-liveness-is-a-collection-question.md) — a name match cannot see shadowing, uncalled factories, or getfixturevalue.
- [Whole-tree pytest needs importlib](whole-tree-collection-needs-importlib.md) — nine repeated basenames and no __init__.py; also needs PYTHONPATH=lib/python:scripts.
- [A push solves one stack's issues](a-push-solves-every-open-issue-of-one-stack.md) — batch by workflow stack, never by count; tests and fix in one commit; shared paths go alone.
- [An issue is closed by its commit](an-issue-is-closed-by-its-commit.md) — one `Closes #N` line per issue in the commit that solves it; `Closes #1 and #2` leaves #2 open.
- [Confirming a push closed its issues](confirming-a-push-closed-its-issues.md) — once the runs are clean, check each issue closed and close by hand where it did not take.
- [A rejected push is fixed forward](a-rejected-push-is-fixed-forward.md) — a red run gets a follow-up commit, never an amend and force-push; read the whole failed log first.
- [Fixing a red run](fixing-a-red-run.md) — the session whose push's run goes red fixes it, caused or inherited, in a push of its own before the next batch.
- [One question at a time](one-question-at-a-time.md) — one plain question per message; queue the rest as tasks and ask them one by one.
- [Issues have no house style](issues-have-no-house-style.md) — write an issue however it reads best; the one rule is a header per part, never a bolded first sentence.
- [New checks are their own repo](new-assert-checks-are-their-own-repo.md) — a standalone 10U-Labs package on PyPI, cloned from the newest sibling; never a script under scripts/.
