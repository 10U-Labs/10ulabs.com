# Memories

- [Commits go straight to main](commits-go-straight-to-main.md) — no branches, no PRs; CI only runs on main.
- [Don't verify locally](do-not-run-test-suites-locally.md) — push and let CI run the suites; local runs waste tokens.
- [Memories live in .claude/memories](memories-live-in-dot-claude-memories.md) — autoMemoryDirectory overrides the user-scoped default path.
- [Lint jobs take whole roots](lint-jobs-take-whole-roots.md) — src/ lib/, scripts/ lib/, test/ lib/ across all six jobs; never path lists.
- [Tests are written before source](tests-are-written-before-source.md) — TDD; a test may name a file that does not exist yet, but read it via a fixture, never at module level.
- [Fixture liveness needs a collection](fixture-liveness-is-a-collection-question.md) — a name match cannot see shadowing, uncalled factories, or getfixturevalue.
- [Whole-tree pytest needs importlib](whole-tree-collection-needs-importlib.md) — nine repeated basenames and no __init__.py; also needs PYTHONPATH=lib/python:scripts.
- [New checks are their own repo](new-assert-checks-are-their-own-repo.md) — a standalone 10U-Labs package on PyPI, cloned from the newest sibling; never a script under scripts/.
