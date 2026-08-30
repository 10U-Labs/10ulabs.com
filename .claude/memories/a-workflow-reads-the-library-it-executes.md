# A workflow reads the library it executes

## Table of Contents

- [The rule](#the-rule)
- [What "its own source" was read to mean](#what-its-own-source-was-read-to-mean)
- [A workflow that deploys no Python still gains the source passes](#a-workflow-that-deploys-no-python-still-gains-the-source-passes)
- [`test_fixtures` is the case that forced it](#test_fixtures-is-the-case-that-forced-it)
- [Ten workflows reading one package is the rule working](#ten-workflows-reading-one-package-is-the-rule-working)
- [The `paths` filter carries the same set](#the-paths-filter-carries-the-same-set)
- [Working out what a workflow executes](#working-out-what-a-workflow-executes)
- [Related notes](#related-notes)

## The rule

A workflow's static analysis reads four things: its own deployed source, its own test subtree, every package under `lib/python/` that the workflow executes, and every suite under `test/lib/python/` that covers one of those packages. All four are named in the argument lists of the jobs the file already carries. The library packages join the deployed source in `pylint-source`, `mypy-source` and `copy-paste-source`; their suites join the workflow's own tests in `pylint-tests`, `mypy-tests` and `copy-paste-tests`. Nothing new is added to the file and no job is created — the lists inside the existing jobs grow, and the same lists appear again in the `assert-no-inline-directives` job, which names every path the workflow reads at all.

The library is on the import path of the test passes either way, and that is a separate thing from being read. `PYTHONPATH=lib/python:scripts` is what lets the linter resolve `import test_fixtures` in a test file it is reading; naming `lib/python/test_fixtures` on the command line is what makes it open `test_fixtures` itself. A workflow that only has the library on its path is a workflow that never reads it.

## What "its own source" was read to mean

The "Four static analysis passes per workflow" section of `CLAUDE.md` says a workflow lints and type-checks "its own source and its own tests", and it does not say what "its own" reaches when a package is executed by ten workflows and owned by none. The narrow reading — a workflow's own source is what sits under its own directory in `src/` — is how all ten deploying workflow files were written, and it is why `39e1ad90` was able to open a hole nothing noticed.

Before that commit, `scripts.yml` was the one file that named the shared library as a target, so the library was read by exactly one workflow and every other workflow merely put it on a path. `#607` scoped `scripts.yml` down to the one program it actually covers, `scripts/invalidate_cloudfront.py`, which is correct for that workflow and left `lib/python/` and `test/lib/python/` read by no linter, no type checker and no duplicate detector anywhere in the repository. Twelve packages went unread and every workflow stayed green, because a workflow reports on what it names and nothing reports on what nothing names. `#622` and `#630` through `#638` are the ten issues that close it, one per deploying workflow.

The rule exists so the hole cannot reopen. Under it the library is read by every workflow that runs it, so no single scoping decision can take it out of CI altogether.

## A workflow that deploys no Python still gains the source passes

`CLAUDE.md` used to say that where the source is Terraform there is nothing for the source passes to read and the workflow carries the two test passes alone. That sentence is gone, and this rule is what replaced it: what the source passes read is the Python the workflow executes, and a Terraform-deploying workflow executes plenty of it.

`bootstrap.yml` is the case. It deploys Terraform and no Lambda source of its own, and it carries a `pylint-source`, a `mypy-source` and a `copy-paste-source` job whose whole argument list is `lib/python/` packages — eight of the nine, being the eight its own suites import. The one left out is `lambda_http`, executed by `api_operational_diagnostics.yml` alone. `www_home.yml` and `www_rack_designer.yml` are in the same position. The alternative, folding the library into the test passes of those workflows, would lint library source under `--recursive=y` with `scripts/` on the import path and would report a library defect under a step named "Run pylint on tests", which is the one thing the four-pass split exists to prevent.

## `test_fixtures` is the case that forced it

`lib/python/test_fixtures/` holds seventeen modules and `test/lib/python/test_test_fixtures/` holds twenty test files covering them. Every deploying workflow executes it, and no workflow says so: the execution is not written in the workflow at all — `test/conftest.py` carries

```python
pytest_plugins = ['test_fixtures.aws']
```

at module level, and pytest loads that module before the first test in any suite below `test/`. A defect in `test_fixtures.aws` can make a whole tier report the wrong answer in every workflow at once, and under the narrow reading of "its own source" no workflow was reading it. `test_fixtures.unit` sat on that line beside it until the commit closing `#567` deleted the last of its fixtures; it is imported by name now rather than loaded as a plugin, and the argument held for it too while it was there.

Check the rule against this one. Every deploying workflow names `test/conftest.py` in its test passes already, so the file that does the importing was being read while the modules it imports were not.

## Ten workflows reading one package is the rule working

`lib/python/repo_utils` appears in the argument list of ten workflows, and that is the intended state rather than duplication to remove. A workflow's run is a gate on that workflow's deployment, and a green run of some other workflow is not: if `www_home.yml` deployed on the strength of `bootstrap.yml` having linted the library, it would be deploying on a check that could be red, skipped, or triggered by a push that never touched the library. The `test-*` jobs that run the library's own suites are placed by the same argument, written down in [a-workflow-runs-the-suites-of-the-packages-it-executes](a-workflow-runs-the-suites-of-the-packages-it-executes.md).

The cost of the repetition is that adding a package to `lib/python/` means editing every workflow that executes it. That is the cost of each workflow being self-sufficient, and it is paid at the one moment a package is added rather than every time one is changed.

## The `paths` filter carries the same set

The same packages and suites are named in the workflow's `paths` filter, so an edit to `lib/python/repo_utils/` starts every workflow that reads it and each of them reports on its own copy of the check. The filter and the argument lists are two lists of the same set, and either one edited without the other is a defect: a package in the filter but not in the lists starts a run that does not read it, and a package in the lists but not in the filter is read only when something else happens to start the workflow. Checking one against the other is the last step of any change to either.

## Working out what a workflow executes

Read the imports, not the directory names. A workflow executes a package if the Lambda source it deploys imports it, if any suite it runs imports it, or if `test/conftest.py` or a `conftest.py` above its subtree imports it — the last being how `test_fixtures` reaches everything. `git ls-files lib/python | awk -F/ '{print $3}' | sort -u` is the list to check against, since a working copy carries `__pycache__` directories for packages git no longer has; see [enumerate-a-directory-from-git](enumerate-a-directory-from-git.md).

The suite for a package is `test/lib/python/test_<package>`.

## Related notes

The running half of this rule is [a-workflow-runs-the-suites-of-the-packages-it-executes](a-workflow-runs-the-suites-of-the-packages-it-executes.md): the same set of packages and suites, run as `test-*` jobs instead of read. The four jobs this rule fills in are [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md). Reading the result is [verification-in-ci-only](verification-in-ci-only.md), and answering a red one is [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
