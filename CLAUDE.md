# Working in 10ulabs.com

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Commits](#commits)
    - [A rejected push is fixed forward](#a-rejected-push-is-fixed-forward)
    - [One issue, one commit](#one-issue-one-commit)
    - [Straight to main](#straight-to-main)
    - [The skip ci directive](#the-skip-ci-directive)
  - [Comments](#comments)
    - [Nothing carries a comment or a docstring](#nothing-carries-a-comment-or-a-docstring)
    - [What a comment was about to say](#what-a-comment-was-about-to-say)
  - [Issues](#issues)
    - [An issue on disk goes stale](#an-issue-on-disk-goes-stale)
    - [An issue states one solution](#an-issue-states-one-solution)
    - [Enumerate a directory from git](#enumerate-a-directory-from-git)
    - [File what the sweep turns up](#file-what-the-sweep-turns-up)
    - [Placing an issue in the queue](#placing-an-issue-in-the-queue)
    - [The seven sections](#the-seven-sections)
    - [Two sections for everything outside the program](#two-sections-for-everything-outside-the-program)
    - [Why static analysis is asked separately](#why-static-analysis-is-asked-separately)
  - [Markdown](#markdown)
    - [No column limit](#no-column-limit)
  - [Tests](#tests)
    - [An empty conftest stays](#an-empty-conftest-stays)
    - [Cover every tier the change touches](#cover-every-tier-the-change-touches)
    - [Test first](#test-first)
    - [The tenets are generic](#the-tenets-are-generic)
    - [The tree splits on deployment phase](#the-tree-splits-on-deployment-phase)
    - [Where test code that is not a test goes](#where-test-code-that-is-not-a-test-goes)
  - [Verification](#verification)
    - [A push starts more than one workflow](#a-push-starts-more-than-one-workflow)
    - [A workflow runs the suites of the packages it executes](#a-workflow-runs-the-suites-of-the-packages-it-executes)
    - [CI is the source of truth](#ci-is-the-source-of-truth)
    - [Finding the run](#finding-the-run)
    - [Four passes read the packages the workflow executes](#four-passes-read-the-packages-the-workflow-executes)
    - [Four static analysis passes per workflow](#four-static-analysis-passes-per-workflow)
    - [Path filters are not shell globs](#path-filters-are-not-shell-globs)
- [Notes](#notes)
  - [Where a new convention goes](#where-a-new-convention-goes)

## Overview

These are the standing conventions for working in this repository. Each section links the longer write-up behind it, one note per topic under `.claude/memories/`; [.claude/memories/README.md](.claude/memories/README.md) indexes them all.

A section here states a rule, a trap or the reason behind one. It does not restate what a file in the tree already says: an inventory copied into this file is a second copy that goes stale with nothing to catch it, and `#549`, `#553`, `#554`, `#584` and `#600` were all filed to repair one. Where the answer is in a workflow file or a tenet, this file points at it rather than paraphrasing it.

## Conventions

### Commits

Longer: [commit-straight-to-main](.claude/memories/commit-straight-to-main.md), [a-rejected-push-is-fixed-forward](.claude/memories/a-rejected-push-is-fixed-forward.md), [never-write-the-skip-ci-brackets-in-prose](.claude/memories/never-write-the-skip-ci-brackets-in-prose.md).

#### A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push: `main` is published by the time the run reports, and rewriting it discards what was tried. Every static-analysis check here is a job of its own and the jobs run in parallel, so a rejected run names every check that failed rather than the earliest one. Read the run for that full list rather than guessing at it, and answer all of it in one follow-up commit.

#### One issue, one commit

One issue is solved by one commit and one push, and the commit closes its issue in the message: `Closes #490` in `31f0066f`, or the qualified `Fixes <owner>/<repo>#<n>` that `1e45d1f9` carries when the issue lives in another repository. That line is what drains the queue — an issue solved by a push that does not carry it stays open and is picked up again on the next pass. An issue that cannot be done in one commit is two issues, and filing the second is the answer rather than spreading one issue across pushes.

#### Straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. There is no pull-request buffer, so CI is the only review there is and the tests land in the same commit as the code they cover.

#### The skip ci directive

The literal `[skip ci]`, brackets included, goes in a commit message only when that push is meant to start nothing. GitHub scans the whole raw message rather than the subject line, so a body that merely names the directive — reporting what an earlier commit did with it — suppresses every workflow its own diff was due to start, which is how `0463bad9` landed 486 `pylint` fixes and nine edited workflow files with no run having read them. Write `skip ci` without the brackets when describing another commit's use of it; quoting the string, indenting it or wrapping it in backticks does not break the match, because the scan reads characters rather than markup.

### Comments

Longer: [nothing-carries-a-comment-or-a-docstring](.claude/memories/nothing-carries-a-comment-or-a-docstring.md).

#### Nothing carries a comment or a docstring

No file this repository lints carries a comment or a docstring: no `#` and no module, class or function docstring in Python, no `#` in a workflow file, no `#`, `//` or `/* */` in OpenTofu, no `//` or `/* */` in JavaScript. `assert-no-comments` is a job in each of the twelve workflow files and is in each `reconciliation` `needs:` list, so a deployment is gated on it; the twenty-two `pylint-source` and `pylint-tests` jobs disable the three `missing-*-docstring` checkers so that pylint does not demand back what that job refuses. A `.md` file is never read, because prose is the content of a markdown file rather than a gloss on a line of code. Prose beside code is never checked by anything, so it stops being true with nothing to say when, and a rename is where that costs first: every sentence naming the old identifier is then wrong, in files the rename never touched, and the diff gives no way to find them. `#652`, `#653` and `#655` were three such findings, all made by a person reading rather than by a job.

#### What a comment was about to say

A comment is about to say what the code does, why it is the way it is, or that a value is required, and each has somewhere better to go: the first is the name, and a name that does not say it is the thing to change; the second is the commit message and the issue, which are dated and attached to a change where a comment sits beside a line claiming to describe it forever; the third is a test, which goes red when it stops being true. That is why commit bodies here are long. An assignment to `__doc__` is code and stays, and a `#` inside a string literal is not a comment.

### Issues

Longer: [how-issues-are-written](.claude/memories/how-issues-are-written.md), [an-issue-states-one-solution](.claude/memories/an-issue-states-one-solution.md), [file-what-the-sweep-turns-up](.claude/memories/file-what-the-sweep-turns-up.md), [an-edge-is-only-a-true-block](.claude/memories/an-edge-is-only-a-true-block.md), [enumerate-a-directory-from-git](.claude/memories/enumerate-a-directory-from-git.md).

#### An issue on disk goes stale

A filed issue is written against the tree as it stood, and the tree moves. Check its claims against the repository before working it or editing it, and correct what has gone stale as part of picking it up.

#### An issue states one solution

An issue is definitive. Its `Proposed Solution` names one change — this function, this file, this algorithm — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader; an issue that ends with something still to decide is not finished. Where a draft reaches a genuine fork, stop and ask which branch and then write down the branch that came back, so the asking happens before the filing rather than inside the body. Naming the rejected alternative and why it lost is still worth writing, because it stops the same ground being covered twice; what is not allowed is leaving the choice open. For issues already on disk that carry an either, do not pick: ask which one before editing a file, however clearly the text leans toward one of them, and ask before there is a draft, because a draft turns the question into a request to approve what is already done.

#### Enumerate a directory from git

When an issue body states what a directory holds — a count of its entries, a list of them, or the name of one — enumerate it with `git ls-files` rather than with `ls` or a file browser. A working copy carries ignored build artifacts that git will not report, so a package deleted from the repository goes on reading as a live one to anything that looks at the disk. `9086acda` deleted `lib/python/runner_labels/` and left the directory standing on a `__pycache__` that `.gitignore` covers, `git status` stayed clean throughout, and nine issue bodies then counted thirteen packages under `lib/python/` where git had twelve. `git status --ignored` is the form that shows what the plain one suppresses.

#### File what the sweep turns up

A defect found while working on something else is filed in the same turn it is found, with a `blocked_by` edge if something genuinely waits on it, rather than named in the reply and left for the user to ask for. A reply is not a record and does not outlive the session. Neither of the two reasons for holding one back survives contact: a fork in how to fix it is a reason to ask which branch and then file, since the fork says nothing about whether the defect is real, and a fix that is not yet specifiable is the work rather than a reason to defer it. A sweep that turns up five defects files five issues.

#### Placing an issue in the queue

A filed issue is placed in the queue before the work goes on, and a `blocked_by` edge is written only where the block is real: where the issue in hand, or another open issue, cannot be finished until the new one is. Where nothing waits on it, it is filed with no edge, which is a finished placement rather than a missing one. An ordering is not a dependency, and an edge written to give an issue a place in the queue is a false statement about the work that the next reader has to take at face value. `.claude/skills/autopilot/SKILL.md` states the two cases, the test that decides them, and the `gh api` calls that write and remove an edge.

#### The seven sections

An issue about the program has seven sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?", "Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?", "Proposed Solution". Every such issue has all seven; where a tier or a job does not exist for the part of the program in question, saying so is the finding rather than a reason to drop the section. The regression section names the coverage owed, each test by its tier and its assertion and each job by what it would refuse, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph.

#### Two sections for everything outside the program

The five sections between the first and the last belong to the program and to nothing else. The program is what a test tier can run: `src/`, `lib/python/`, `lib/terraform/` and `scripts/`. An issue about the configs in `etc/`, the workflow files in `.github/` or the documentation in `docs/` has two sections, "Problem" and "Proposed Solution", and owes no tests — a test over a file no tier runs only reads a value back and asserts what it just read. Static analysis does reach those files, since the YAML linter reads every workflow file and the markdown linter every document, and the static analysis section stays with the program regardless: the five travel together, and an issue that carries one of them carries all five. Most of the open queue is of this second kind, so the split is by directory and there is nothing to weigh. `test/` falls on both sides: the machinery a tier runs on is program code and gets seven, conftest fixtures included, because it can make a whole tier report the wrong answer; the assertions themselves get two, since asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.

#### Why static analysis is asked separately

Static analysis is the half of CI that reads the source without running it, and it is asked about separately because it catches a different kind of defect from any tier. A tier executes the program and judges what comes back, so it can only catch what a caller could observe. A job reads the text and refuses a shape, so it catches the defect wherever it appears rather than wherever a test happens to reach, and it is the right answer whenever the defect is one a rule could have named. The jobs are every check in a workflow that reads the source without running it; the deployment job is not one of them, because it plans and applies against the cloud provider.

### Markdown

Longer: [markdown-is-not-hard-wrapped](.claude/memories/markdown-is-not-hard-wrapped.md).

#### No column limit

Markdown is not hard-wrapped, and neither is the body of a commit message. There is no column limit on `.md` files here, none on the bodies of GitHub issues and none on the paragraphs of a commit: write each paragraph as one line and let the reader wrap it. The subject line is the one thing that stays short, because `git log --oneline` and GitHub both truncate it. Nothing enforces this — the markdown linter runs with the line-length rule disabled and no check reads a commit message at all — so match this rule rather than the file or the commit next to you.

### Tests

Longer: [tdd-workflow](.claude/memories/tdd-workflow.md), [read-test-tenets-first](.claude/memories/read-test-tenets-first.md), [tenets-are-generic](.claude/memories/tenets-are-generic.md), [the-test-tree-splits-on-deployment-phase](.claude/memories/the-test-tree-splits-on-deployment-phase.md), [test-code-is-placed-by-how-many-suites-use-it](.claude/memories/test-code-is-placed-by-how-many-suites-use-it.md), [a-conftest-is-emptied-never-deleted](.claude/memories/a-conftest-is-emptied-never-deleted.md).

#### An empty conftest stays

A `conftest.py` whose last fixture goes is emptied to zero bytes and left where it is, never deleted. The empty file is what tells whoever writes the next fixture that this level exists to hold one, and whoever writes it is usually a session like this one; left to itself a session writes setup into the test file already open in front of it, and the same setup is then copied into every other test file that needs it. Empty means empty, with no docstring and no comment explaining the emptiness, because a file that still says something has to be read before it can be found to hold nothing. Leaving it in place also costs nothing elsewhere, where deleting it would mean editing every workflow that names its path in a trigger or in a list of files handed to a linter.

#### Cover every tier the change touches

Read `docs/tenets/tests/` before implementing. Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest. `Assert one assert per pytest` is a step in every workflow that runs tests, so a test with two asserts fails the push rather than being noticed in review.

#### Test first

We do TDD: the test is written first, then the code that makes it pass. Test-first means authoring order — the red and the green observations belong to CI, since nothing runs locally.

#### The tenets are generic

The four tier files under `docs/tenets/tests/` — `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md` — are tenets, not a description of the suite. They name no language, tool, directory or resource, because the repository already states all of that and a second copy drifts. When a tenet and the repository disagree, the repository is what changes; editing a tenet to match the code is backwards.

#### The tree splits on deployment phase

A subsystem that deploys is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when there is a test to put in it. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call. Code under `lib/` deploys nothing of its own and so carries no such split: its tests mirror the package and stop. What decides the tier is what the test reads, not how end-to-end it looks. Which directory holds what is read from the tree with `git ls-files`.

#### Where test code that is not a test goes

Test code that is not itself a test — a fixture, a mock factory, a loader — is written once, and what decides where it goes is how many suites call it rather than what it is named after. A fixture is written at the highest conftest level where it still applies and inherited from there, because a copy one level down is what drifts. A helper several suites call belongs in `lib/python/` whatever subsystem its name mentions, and one a single suite calls belongs beside that suite however general it sounds; a module at the root of the test tree that only one subsystem imports is the shape to avoid. So writing a new fixture starts with reading: the conftest files above the one in hand, and the packages under `lib/python/`, which is what the shared library already holds.

### Verification

Longer: [verification-in-ci-only](.claude/memories/verification-in-ci-only.md), [find-a-run-by-the-full-hash](.claude/memories/find-a-run-by-the-full-hash.md), [four-static-analysis-passes-per-workflow](.claude/memories/four-static-analysis-passes-per-workflow.md), [a-workflow-reads-the-library-it-executes](.claude/memories/a-workflow-reads-the-library-it-executes.md), [a-workflow-runs-the-suites-of-the-packages-it-executes](.claude/memories/a-workflow-runs-the-suites-of-the-packages-it-executes.md).

#### A push starts more than one workflow

A push starts every workflow whose `paths` filter the commit touches, and the change is done when each of them is green rather than when the first one is.

#### A workflow runs the suites of the packages it executes

A workflow runs the suite of every package under `lib/python/` that the workflow executes, each in a job of its own named after its package and carrying the `--cov=<package> --cov-branch --cov-report=term-missing --cov-fail-under=100` gate `a2558ccc` gave the ten jobs in `api_common_routing.yml`. What a workflow executes is the same set the static analysis reads. The reason is that the workflow runs the code and the code can make its run red: a defect in a package a workflow imports is reported by that workflow either way, and the job is what makes it reported against the package that broke rather than against whichever of the workflow's own suites reached the broken line first. A workflow that deploys is gated twice over, its `reconciliation` job being what stops an apply over a broken library; a workflow that deploys nothing carries the jobs on the first reason alone, which is the case `scripts.yml` was left in when `39e1ad90` deleted its twelve `test-*` jobs and the ten issues that put them back elsewhere all argued from the deployment gate. A package reached only through another package travels with it, so the workflow that runs the reaching package's suite runs the reached package's suite too: `boto_mocks` is imported outside test code by one file only, `lib/python/test_fixtures/unit.py`, and without the corollary its suite would run in no workflow at all. The `paths` filter carries the same set, so an edit to a package starts every workflow that runs its suite.

#### CI is the source of truth

CI is the source of truth. Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list` / `gh run watch` / `gh run view --log-failed`. Local runs cost tokens and pull in dependencies this machine does not otherwise need; CI is free and checks every gate at once. Reading the code locally is still right and cheap — `grep` and file reads are how the useful findings surface, and two suites asserting opposite things about one setting is the kind of thing only reading catches. The line is at executing checks: no virtualenv, no dependency install, no `pytest` or `pylint` run to confirm what CI confirms for free.

#### Finding the run

Find the run by the full forty-character hash from `git rev-parse HEAD`. `gh run list --commit` silently returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started, so anything that polls should list recent runs and match `headSha` by prefix locally.

#### Four passes read the packages the workflow executes

A workflow's static analysis reads its own deployed source, its own test subtree, every package under `lib/python/` that the workflow executes and every suite under `test/lib/python/` that covers one of them, all four named in the argument lists of the jobs the file already carries rather than in jobs added for the purpose. What a workflow executes is what its deployed source imports, what its own suites import, and what `test/conftest.py` loads as a plugin for every suite in the tree — so `test_fixtures` belongs to every deploying workflow whether or not that workflow names it anywhere else. Having the library on the test passes' import path is not reading it: `PYTHONPATH=lib/python` resolves the import, and naming `lib/python/test_fixtures` on the command line is what makes the linter open the package. A package executed by ten workflows is read by all ten, and that repetition is the rule working rather than duplication to remove, since a green run of a workflow this one does not depend on is not a gate on this one's deployment. The library is owned by no workflow, and one workflow reading it for everybody is what stood until `39e1ad90` scoped `scripts.yml` down under `#607` and left all twelve packages and their suites read by no linter, type checker or duplicate detector anywhere in the repository, with every workflow still green.

#### Four static analysis passes per workflow

A workflow lints and type-checks its own source and its own tests in four passes — the linter over the source, the linter over the tests, the type checker over the source, the type checker over the tests — each a job of its own, so a red run says which half of which tool broke before a log is opened. The split is what keeps the test import path, which needs the shared library and `scripts/` on it, off the source passes. Every workflow carries all four, one whose deployed source is Terraform included: what its source passes read is the shared library it executes, which is why `bootstrap.yml` has a `pylint-source`, a `mypy-source` and a `copy-paste-source` job while deploying no Python of its own. Adding a workflow means adding all four, since nothing else in the repository notices a tool that is not being run.

#### Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob and not a directory glob. GitHub reads `**` as any run of characters, `/` included, so `**/*.md` needs a slash to match and reaches no file at the root of the repository: it covers `docs/tenets/tests/UNIT_TESTS.md` and misses `CLAUDE.md`. The form that reaches both is `'**.md'`, quoted because a bare `*` opens a YAML alias. This is the opposite of how the same two patterns read in `node`, where `**/` matches zero directories and both forms reach the root, so a filter copied from a lint command covers less than the command does.

## Notes

### Where a new convention goes

A convention learned in a session belongs in this repository: a paragraph in this file and a topic file under `.claude/memories/`, linked from both indexes and carrying a table of contents and `##` sections like every note beside it — or a file under `docs/tenets/` when it says what a kind of work is for rather than how this repository does it. The session tool's own memory directory under the home directory is one machine's unversioned files, and a rule kept in both places drifts with nothing to signal it, which is why the local copy of the CI rule was deleted when these notes were written. Keep there only what is true of that machine alone.
