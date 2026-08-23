# Test-driven development

## Table of Contents

- [The rule](#the-rule)
- [What test-first means here](#what-test-first-means-here)
- [Coverage at every tier](#coverage-at-every-tier)

## The rule

We do TDD in this repository. Write the test first, then the production code that makes it pass.

## What test-first means here

Test-first here means authoring order, not a local red-green loop. The failing observation and the passing one both belong to CI, because nothing is run locally — see [verification-in-ci-only](verification-in-ci-only.md). Put the tests and the implementation in the same commit, since a commit goes straight to `main` with no pull-request buffer to hold a red state — see [commit-straight-to-main](commit-straight-to-main.md).

## Coverage at every tier

Coverage is not one test file. Add the test at each tier the change touches, which means reading the tenets before writing anything — see [read-test-tenets-first](read-test-tenets-first.md) — and putting each test in the tier its subsystem actually has, which is not the same shape everywhere: see [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md).
