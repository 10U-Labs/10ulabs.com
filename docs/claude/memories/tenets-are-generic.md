# The tenets are generic, and the repository follows them

`docs/tenets/tests/` holds tenets, not documentation of the test suite. A tenet is true whatever the repository holds: it names no language, no tool, no directory, no resource and no count. The repository is what has to change to match, never the other way round.

So a tenet says "one test file per unit of source, named for the unit it covers", not which files cover which module. It says "a copy-paste gate runs at a zero-tolerance threshold", not which tool runs it. Layout, tool names, step names, inventories of existing utilities and counts of existing tests all belong to the repository, which already states them and states them correctly. Anything written into a tenet that the repository also states is a copy, and a copy drifts with nothing to signal it.

The four tier files here hold to that. `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md` mention no directory, no `pytest`, no `terraform` and no module name. When one of them and the tree disagree, the tree is what changes; editing a tenet to match the code is backwards.

`OVERVIEW.md` beside them is the opposite kind of document and is read the opposite way. It names the conftest levels, the modules under `lib/python/`, the four static-analysis step names and the imports each provides — all of it a description of this suite — so where it and the tree disagree, `OVERVIEW.md` is what is out of date. It already is: its test hierarchy diagram is built around `test/api/backend/`, and there is no such directory. The tree has `test/api/common/`, `test/api/endpoints/` and `test/api/operational/`.

Keeping it is still worth it, because what it indexes — the fixtures in `lib/python/test_fixtures/`, `boto_mocks/`, `terraform_config/`, `naming_conventions/` and the rest — is the answer to "does this already exist", and that is expensive to rediscover. Read it for the inventory, not for the layout, and check what it says against the tree before relying on it.

The failure this note exists to prevent is the one in `10U-Labs/wan-synthesizer` on 2026-07-29, where an issue titled "Align docs/tenets/test/ to this repo" was taken at face value and the five documents were rewritten to describe that repository — its directory tree, its utility modules, its workflow step names. Removing what a repository does not use is right; replacing it with a description of what it does use inverts the relationship. Pair with [read-test-tenets-first](read-test-tenets-first.md).
