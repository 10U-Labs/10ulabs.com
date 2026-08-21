# A rejected push is fixed forward

When a push fails CI, fix it in a follow-up commit. Do not amend and force-push. `main` is the only branch and it is already published by the time the run reports, so rewriting it discards the history of what was actually tried.

This puts two standing rules in tension, and how the tension resolves is worth stating rather than rediscovering. An issue is meant to be solved in a single push, and verification happens only in CI. The static-analysis checks here are steps of a single `deploy` job — `Assert no linter config files`, `Assert no inline lint disables`, `Assert one assert per pytest`, `Linting YAML files`, four `pylint` and `mypy` steps, two `jscpd` steps, `Terraform Format Check`, `Run tflint` — and a job stops at its first failing step. So a change carrying several independent findings surfaces the first one, and nothing about the ones behind it, until that one is fixed.

Running the analysers locally would collapse that to one push, and it is the obvious suggestion. It has been made and declined: no local runs, of anything, including linters — see [verification-in-ci-only](verification-in-ci-only.md). When the two rules collide, CI-only is the one that holds and the extra commits are the accepted cost. Do not propose local linting as a way to honour the single-push rule, and do not treat a static-analysis rejection as licence to rewrite the commit.

What is worth doing instead is reading the whole failed step rather than its first line — one `pylint` step reports every finding it has, and the step after it stays unread until this one passes — and sweeping the change for other instances of the same shape before pushing the fix. A fix that also clears every sibling instance turns two cycles into one without running anything here.

`10U-Labs/wan-synthesizer` answered the same tension differently, by splitting each check into a job of its own so one run reports every finding at once. That is available here and is not done; until it is, the sweep is what stands in for it.
