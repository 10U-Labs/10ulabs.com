# A rejected push is fixed forward

## Table of Contents

- [The rule](#the-rule)
- [The tension with the single-push rule](#the-tension-with-the-single-push-rule)
- [Why local linting is not the answer](#why-local-linting-is-not-the-answer)
- [Let the run name every failing job](#let-the-run-name-every-failing-job)
- [Where the tension came from](#where-the-tension-came-from)

## The rule

When a push fails CI, fix it in a follow-up commit. Do not amend and force-push. `main` is the only branch and it is already published by the time the run reports, so rewriting it discards the history of what was actually tried.

## The tension with the single-push rule

This puts two standing rules in tension, and how the tension resolves is worth stating rather than rediscovering. An issue is meant to be solved in a single push, and verification happens only in CI. Every static-analysis check here is a job of its own — `assert-no-inline-directives`, `assert-no-linter-config-files`, `assert-one-assert-per-pytest`, `copy-paste-source`, `copy-paste-tests`, `mypy-source`, `mypy-tests`, `pylint-source`, `pylint-tests`, `terraform-format`, `tflint` and `yamllint` — and the jobs start together. So a change carrying several independent findings surfaces all of them at once, in one run, and each failing job reports its own conclusion.

## Why local linting is not the answer

Running the analysers locally would collapse that to one push, and it is the obvious suggestion. It has been made and declined: no local runs, of anything, including linters — see [verification-in-ci-only](verification-in-ci-only.md). When the two rules collide, CI-only is the one that holds and the extra commits are the accepted cost. Do not propose local linting as a way to honour the single-push rule, and do not treat a static-analysis rejection as licence to rewrite the commit.

## Let the run name every failing job

What is worth doing instead is letting the run say what failed rather than guessing at it. `gh run view <id> --json jobs` lists every job and its conclusion, so the failing checks are named outright, and `gh run view --log-failed` prints their output; one `pylint` job reports every finding it has. A follow-up commit that answers every named job turns two cycles into one without running anything here.

## Where the tension came from

The checks were once steps of a single `deploy` job, which stopped at the first failing step and so reported one finding at a time. `c4273c78`, "Give every check in the ten deploying workflows a job of its own", ended that, and no workflow file here has a job named `deploy` any more. What remains of the tension is only that the findings arrive after the push rather than before it.
