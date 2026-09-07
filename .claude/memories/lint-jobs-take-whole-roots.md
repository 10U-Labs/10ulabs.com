---
name: lint-jobs-take-whole-roots
description: All six per-workflow Python lint jobs are scoped to whole roots — src/ lib/, scripts/ lib/, test/ lib/ — never path lists.
metadata:
  type: project
---

# Lint jobs take whole roots, not path lists

The six Python lint jobs in each of the eleven workflows (`copy-paste-source`, `copy-paste-tests`, `pylint-source`, `pylint-tests`, `mypy-source`, `mypy-tests`) all share one scope rule:

| side | ten stack workflows | `scripts.yml` |
| --- | --- | --- |
| source | `src/ lib/` | `scripts/ lib/` |
| tests | `test/ lib/` | `test/ lib/` |

`lib/` is on **both** sides. Landed in d6819e86 (`jscpd`, #773/#777), 4885d4c7 (`pylint`, #778) and 4ddb62c9 (`mypy`, #779).

**Why:** each job used to get the shared `lib/python` packages plus exactly one stack, so the cross-file checks — `jscpd` at `--threshold 0` and `pylint`'s `R0801` under `--fail-on=C,R,W` — were never handed two stacks and could not fire across them. A 47-line clone (#776) and a three-way `ROUTE_MAP` clone sat in the gap. Path lists also meant a new stack was uncovered until someone remembered to extend eleven lists, and that what `lib/` got checked for differed per workflow.

**How to apply:** never reintroduce a path list. A new stack needs no lint-job edit. Two gotchas when touching the `mypy` jobs:

- `--explicit-package-bases` is **required** on both `mypy` jobs. Every lambda entry point is `handler.py` and no `lambda/` dir has an `__init__.py`, so mypy's default naming maps all eight to the bare module `handler` and aborts with `Duplicate module named "handler"` before checking anything. The flag names modules from the roots instead (`src.api...lambda.handler`); `lib/python` is on `MYPYPATH`, so `lambda_response` and friends keep their bare names.
- `mypy-tests` needs `dnspython` installed, because `test/` includes `test/bootstrap/post_deployment/e2e/`, which imports `dns.resolver`. `mypy-source` does not.

The `paths:` triggers were deliberately left per-stack in all three commits, so a change to one stack can redden another workflow's lint job without triggering it. Widening the triggers is a separate decision across all six jobs.

See [[commits-go-straight-to-main]].
