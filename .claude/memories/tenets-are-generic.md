# The tenets are generic, and the repository follows them

## Table of Contents

- [What a tenet is](#what-a-tenet-is)
- [What belongs to the repository instead](#what-belongs-to-the-repository-instead)
- [The four tier files hold to it](#the-four-tier-files-hold-to-it)
- [The failure to watch for](#the-failure-to-watch-for)

## What a tenet is

`docs/tenets/tests/` holds tenets, not documentation of the test suite. A tenet is true whatever the repository holds: it names no language, no tool, no directory, no resource and no count. The repository is what has to change to match, never the other way round.

## What belongs to the repository instead

So a tenet says "one test file per unit of source, named for the unit it covers", not which files cover which module. It says "a copy-paste gate runs at a zero-tolerance threshold", not which tool runs it. Layout, tool names, step names, inventories of existing utilities and counts of existing tests all belong to the repository, which already states them and states them correctly. Anything written into a tenet that the repository also states is a copy, and a copy drifts with nothing to signal it.

## The four tier files hold to it

The four tier files here hold to that. `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md` mention no directory, no `pytest`, no `terraform` and no module name. When one of them and the tree disagree, the tree is what changes; editing a tenet to match the code is backwards.

## The failure to watch for

`6ecd5424` is the removal case working: both integration tenets promised that a layer which fails stops the ones above it, no invocation of either tier had ever passed `--exitfirst` or anything like it, and the behaviour had been dropped deliberately rather than lost. The clause came out and nothing went in its place, because writing down that every layer now runs and the lowest failure names the cause would have been a description of the implementation wearing a tenet's clothes.

The failure to watch for is an issue asking to align the tenets to this repository, taken at face value: the four tier files get rewritten to describe the directory tree, the utility modules and the workflow step names, and the relationship inverts. Removing from a tenet what this repository does not use is right; replacing it with a description of what this repository does use is not. Pair with [read-test-tenets-first](read-test-tenets-first.md).
