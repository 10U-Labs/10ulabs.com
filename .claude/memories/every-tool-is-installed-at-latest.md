# Every tool is installed at latest

## Table of Contents

- [The rule](#the-rule)
- [What is installed](#what-is-installed)
- [Why a pin is worse than the surprise it prevents](#why-a-pin-is-worse-than-the-surprise-it-prevents)
- [The live example](#the-live-example)
- [What is not a pin](#what-is-not-a-pin)
- [Answering a red run that a release caused](#answering-a-red-run-that-a-release-caused)
- [The issue that proposed the opposite](#the-issue-that-proposed-the-opposite)
- [Related notes](#related-notes)

## The rule

Every package a workflow installs is named with no version specifier, so each job installs whatever the index is serving when it runs. No `==`, no `<`, no `@version`, and no requirements file holding any of those. This is the policy rather than an oversight, and it applies to a package added tomorrow as much as to the ones already there.

## What is installed

Seventeen packages come from `python3 -m pip install`: `assert-no-comments`, `assert-no-inline-directives`, `assert-no-linter-config-files`, `assert-one-assert-per-pytest`, `assert-pytest-fixture-name-is-needed`, `boto3`, `boto3-stubs`, `botocore`, `dnspython`, `mypy`, `pylint`, `pytest`, `pytest-cov`, `python-hcl2`, `requests`, `types-requests`, `yamllint`. Three come from `npm install -g`: `jscpd`, `jsonlint`, `markdownlint-cli`. Three more come from the `npm install --no-save` in `www_rack_designer.yml`: `eslint`, `@eslint/js`, `globals`. Read the current set from the files rather than from this list, which is a snapshot: `grep -rn 'pip install' -A 20 .github/workflows/` and `grep -rn 'npm install' .github/workflows/`.

## Why a pin is worse than the surprise it prevents

A pinned checker is a checker that has stopped checking. The five `10U-Labs` tools are written to be extended — a new suffix, a new shape refused, a defect fixed in a reader — and the point of installing them here is that the day a release can see more, this repository is held to it. A pin defers every one of those findings to whenever somebody edits the pin, and nothing schedules that, so the pinned version is the one that was current the day the line was written and the findings accumulate unreported behind it. The same is true of `pylint`, `mypy` and `yamllint`: a release that adds a checker is a check this repository wants, and a bounded specifier like `<8` is a pin with a slower fuse rather than a different kind of thing.

Reproducibility is the price and it is paid knowingly. Re-running a job from three weeks ago does not install what it installed, and a green run is evidence about the commit and the tools of the day it ran rather than about the commit alone. That is accepted here because the tree is small, `main` is the only branch, and the last run is never far behind.

## The live example

`10U-Labs/assert-no-comments` cut `v20260829124358` on 2026-08-29. It replaced the hand-rolled readers with tree-sitter grammars and gave the tool `.ts`, `.tsx`, `.mts` and `.cts`, which it had never read; the next run of `www_home.yml` opened sixty-five files the job had been skipping in silence and refused twenty-three comments that had stood in `main` for months, which is `#690`. No commit here caused that and no diff here showed it. That is the policy working: the comments were always against the rule and the tool had no reader for the files holding them, and an exact pin would have kept them invisible for as long as the pin stood.

## What is not a pin

`src/www/paths/home/package-lock.json` stays, and `www_home.yml` goes on installing from it with `npm ci --prefix src/www/paths/home`. A lockfile pins what deploys — react, vite, and everything else that ends up in `dist/` and is served — rather than what CI refuses, and resolving the application's dependencies fresh on every build is a different question from installing the checkers at latest. The `eslint` that job runs comes out of that lockfile as a consequence of the application depending on it, not as a tool pin.

Everything else that is not a version is also not a pin: `actions/checkout@v4` and `actions/setup-python@v5` are action references, and `python-version: '3.13'` selects an interpreter rather than a package.

## Answering a red run that a release caused

A run that a release in another repository turned red is answered by fixing what it found, in this repository or in the tool's own. The answer is never to add a specifier to the install line, and a session that hits such a run and reaches for a pin has misread the finding as noise. Where the tool itself is wrong, the fix is an issue in the tool's repository, filed from here and named in the `Proposed Solution`.

## The issue that proposed the opposite

`#693` was filed proposing that the seventeen packages it counted as unpinned be pinned exactly, arguing from the `assert-no-comments` release above and from reproducibility. The premise was wrong: the repository's opinion is latest, and the three pins that stood — `jscpd@4.0.5` in twenty-two lines, `'python-hcl2<8'` in six, and `eslint@9 @eslint/js@9` in one — were the exceptions rather than the house style. The issue was rewritten to strip those three and closed by the commit that did it. Do not re-file it.

## Related notes

Reading the run rather than running anything locally is in [verification-in-ci-only](verification-in-ci-only.md), and answering a rejected run with a follow-up commit rather than a force-push is in [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md). Which files each job is handed is in [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md) and [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md).
