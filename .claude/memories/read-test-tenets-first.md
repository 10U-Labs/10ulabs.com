# Read the test tenets first

Before implementing a change, read `docs/tenets/tests/`. Five files sit there and they are not all the same kind of document: `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md` say what each tier is held to and name no tool or directory, while `OVERVIEW.md` describes this suite by name. Which one wins when they disagree with the tree is in [tenets-are-generic](tenets-are-generic.md).

Unit tests alone are not sufficient. Add coverage at every tier the change touches. One assert per pytest, which is not a style preference here: `Assert one assert per pytest` is a step in every workflow that runs tests, which is every one but `documentation.yml`, so a test with two asserts fails the push.

Reading them is the first step of the work, not a check performed afterwards. Pair it with [tdd-workflow](tdd-workflow.md), which decides when the tests get written, and with [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md), which decides where they go.
