# Read the test tenets first

## Table of Contents

- [What to read](#what-to-read)
- [What the tenets require](#what-the-tenets-require)
- [When to read them](#when-to-read-them)

## What to read

Before implementing a change, read [docs/tenets/tests/](../../docs/tenets/tests/). Five files sit there and they are all the same kind of document: the four tier files [UNIT_TESTS.md](../../docs/tenets/tests/UNIT_TESTS.md), [PRE_DEPLOYMENT_INTEGRATION_TESTS.md](../../docs/tenets/tests/PRE_DEPLOYMENT_INTEGRATION_TESTS.md), [POST_DEPLOYMENT_INTEGRATION_TESTS.md](../../docs/tenets/tests/POST_DEPLOYMENT_INTEGRATION_TESTS.md) and [E2E_TESTS.md](../../docs/tenets/tests/E2E_TESTS.md) say what each tier is held to, and [TEST_FIRST.md](../../docs/tenets/tests/TEST_FIRST.md) holds at every tier; none of them names a tool or a directory. That a tenet loses to nothing, the repository being what changes when the two disagree, is in [tenets-are-generic](tenets-are-generic.md).

## What the tenets require

Unit tests alone are not sufficient. Add coverage at every tier the change touches. One assert per pytest, which is not a style preference here: `Assert one assert per pytest` is a step in every workflow that runs tests, which is every one but `documentation.yml`, so a test with two asserts fails the push.

## When to read them

Reading them is the first step of the work, not a check performed afterwards. Pair it with [tdd-workflow](tdd-workflow.md), which decides when the tests get written, and with [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md), which decides where they go.
