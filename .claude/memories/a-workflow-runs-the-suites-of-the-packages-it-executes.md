# A workflow runs the suites of the packages it executes

## Table of Contents

- [The rule](#the-rule)
- [The shape of the job](#the-shape-of-the-job)
- [A workflow that deploys nothing carries the jobs anyway](#a-workflow-that-deploys-nothing-carries-the-jobs-anyway)
- [A package reached through another package travels with it](#a-package-reached-through-another-package-travels-with-it)
- [`test_utils` is not that case](#test_utils-is-not-that-case)
- [One suite run by every workflow is the rule working](#one-suite-run-by-every-workflow-is-the-rule-working)
- [The `paths` filter carries the same set](#the-paths-filter-carries-the-same-set)
- [Working out what a workflow executes](#working-out-what-a-workflow-executes)
- [Related notes](#related-notes)

## The rule

A workflow runs the suite of every package under `lib/python/` that the workflow executes, each suite in a job of its own named after its package. What a workflow executes is what its deployed source imports, what its own suites import, and what `test/conftest.py` loads as a plugin for every suite in the tree.

The reason is that the workflow runs the code and the code can make the run red. A defect in a package a workflow imports is reported by that workflow either way; the job is what makes it reported against the package that broke rather than against whichever of the workflow's own suites happened to reach the broken line first. Without the job, a break in `boto_mocks` surfaces as a failure inside `test_test_fixtures`, or inside a Lambda suite three imports away, and the log has to be read backwards to find out what actually changed.

A workflow that deploys is gated twice over by this, since its `reconciliation` job lists every `test-*` job in `needs:` and is what stops an apply over a broken library.

## The shape of the job

One job per package, named `test-<package>` with the underscores turned into hyphens, running the package's suite under a full branch-coverage gate. `a2558ccc` gave `api_common_routing.yml` the ten jobs the other files were then matched to, and the run step is the same in all of them:

```yaml
      - name: Run repo_utils tests with a full coverage gate
        run: |
          PYTHONPATH=lib/python python3 -m pytest \
            test/lib/python/test_repo_utils/ \
            --confcutdir=test --verbose --pythonwarnings=error \
            --cov=repo_utils \
            --cov-branch \
            --cov-report=term-missing \
            --cov-fail-under=100
```

The coverage gate is over the package rather than over the workflow's own source, so the number a run reports is the library's own and does not move when a Lambda that imports it changes. `naming_conventions` is the one package whose suite is two directories, `test_naming_conventions` and `test_naming_conventions_helpers`; it is still one job, with both paths passed to the one `pytest` invocation and one `--cov=naming_conventions`.

## A workflow that deploys nothing carries the jobs anyway

`#608` through `#617` each put one workflow's `test-*` jobs back, and every one of those ten bodies argued the same narrower thing: that a green run of a workflow this one does not depend on is not a gate on this one's `terraform apply`. That is true, and it is not the whole reason, because it says nothing about a workflow with no apply in it.

`.github/workflows/scripts.yml` is that workflow, and the gap had it in it. `39e1ad90` deleted its twelve `test-*` jobs under `#607`, the ten issues put ten of them back under the ten deploying workflows, and the one file whose jobs had been deleted was reached by none of them, because the deployment-gate argument stops at its door. It executed eight shared-library packages, six of them through the `test/conftest.py` plugin line alone, and ran the suite of none until `3f068a8d` closed `#641`. That file has no `reconciliation` job and never will; its `test-*` jobs stand on the first reason alone, which is the reason that applies everywhere.

## A package reached through another package travels with it

A package reached only through another package travels with it: the workflow that runs the reaching package's suite runs the reached package's suite too.

`lib/python/boto_mocks/` is the case that forced this. Outside test code it is imported by exactly one file, `lib/python/test_fixtures/unit.py`. No Lambda under `src/`, no program under `scripts/` and no suite outside `test/lib/python/test_test_fixtures/` names it. Read narrowly, "the workflow that uses the package" finds no workflow for it, since what the workflows use is `test_fixtures` and `test_fixtures` is what uses `boto_mocks`, and its suite would run nowhere at all. Every landed workflow gives it a job of its own, `scripts.yml` included.

`event_factories` and `urllib_mocks` stood beside it here until the commit closing `#649` deleted both packages and their suites. They reached the workflows the same way until the commit closing `#567` deleted the three fixtures in `unit.py` that read them, and a package the corollary no longer reaches is one nothing imports at all: the answer to that is to delete it, not to keep eleven `test-*` jobs green over it.

Check it against the tree rather than taking it on trust: `git grep -l boto_mocks -- src scripts lib test` names nothing outside `lib/python/boto_mocks/` and `test/lib/python/test_boto_mocks/` but that one `unit.py` and seven files under `test/lib/python/test_test_fixtures/test_integration/`.

## `test_utils` is not that case

`lib/python/test_utils/` is the other package with no consumer of its own, and the corollary does not reach it. Nothing imports it at all, not through another package and not directly, so there is no workflow that executes it and no workflow that owes its suite a job. What it needs is the decision `#603` was filed for, which is whether the package stays at all, rather than a workflow to run its tests in.

## One suite run by every workflow is the rule working

`test/lib/python/test_repo_utils/` is run by nine workflows today and by eleven once `#612` and `#613` land, and that is the intended state rather than duplication to remove. Each workflow's run is a gate on that workflow alone: a workflow that deployed on the strength of another workflow having run the library's suites would be deploying on a check that could be red, skipped, or triggered by a push that never touched the library.

The cost is that adding a package to `lib/python/` means adding a job to every workflow that executes it, paid once when the package is added rather than every time one is changed. This is the running half of the same trade the reading half makes; see [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md).

## The `paths` filter carries the same set

The packages and their suites are named in the workflow's `paths` filter as well, so an edit to `lib/python/repo_utils/` starts every workflow that runs its suite. The filter and the `test-*` jobs are two lists of the same set, and either edited without the other is a defect: a package in the filter with no job starts a run that does not test it, and a job with no entry in the filter runs only when something else happens to start the workflow. Checking one against the other is the last step of any change to either, and the same check is owed against the static analysis argument lists, which carry the same set again.

`test/conftest.py`, `test/__init__.py`, `test/lib/__init__.py` and `test/lib/python/__init__.py` belong in the filter too, since a change to any of them changes what every suite in the tree collects.

## Working out what a workflow executes

Read the imports, not the directory names. A workflow executes a package if the source it deploys imports it, if any suite it runs imports it, if a package it already executes imports it, or if `test/conftest.py` or a `conftest.py` above its subtree imports it — the last being how `test_fixtures`, and through it `boto_mocks`, `lambda_response`, `module_utils` and `terraform_config`, reach every suite in the tree.

`git ls-files lib/python | awk -F/ '{print $3}' | sort -u` is the list to check against, since a working copy carries `__pycache__` directories for packages git no longer has; see [enumerate-a-directory-from-git](enumerate-a-directory-from-git.md). The suite for a package is `test/lib/python/test_<package>`, with `naming_conventions` the exception noted above.

## Related notes

The reading half of this rule is [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md): the same set of packages and suites, named in the argument lists of the static analysis jobs instead of run. The four jobs it fills in are [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md). Reading the result is [verification-in-ci-only](verification-in-ci-only.md), and answering a red one is [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
