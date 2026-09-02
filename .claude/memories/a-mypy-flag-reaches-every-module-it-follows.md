# A mypy flag reaches every module it follows

## Table of Contents

- [The rule](#the-rule)
- [What the eleven commands name and what they read](#what-the-eleven-commands-name-and-what-they-read)
- [The incident](#the-incident)
- [What this means for an issue about a flag](#what-this-means-for-an-issue-about-a-flag)
- [The same trap in the other direction](#the-same-trap-in-the-other-direction)
- [Related notes](#related-notes)

## The rule

A `mypy` command's argument list says where to start, not what will be checked. `mypy` follows every import out of the files it is given and analyses what it finds, and the flags on the command line apply to those modules exactly as they apply to the named ones. `--disallow-untyped-defs` on a command naming only paths under `test/` refuses an unannotated function in `lib/python/` too, because `test/` imports `lib/python/` and `MYPYPATH` resolves it.

So the scope of a change to a `mypy` command is the import closure of the paths it names, and reading the argument list tells you where the reading starts rather than where it stops.

## What the eleven commands name and what they read

Each of the eleven `mypy-tests` commands names a set of paths under `test/` and carries `MYPYPATH=lib/python:scripts`. What it reads is that set plus everything reachable from it: the packages under `lib/python/` those suites import, `scripts/` where a suite imports a script, and the standard library and third-party packages, which are excluded from the flags because they ship their own stubs or are ignored. The count `mypy` prints at the end — `checked 65 source files` for a command naming thirteen paths — is the closure rather than the list.

## The incident

`#575` proposed annotating every function under `test/` and said the fix was "entirely in `test/`". It also stated, of `#744` through `#748`, that "no `mypy-tests` command reads a file outside `test/`, and no `mypy-source` command reads one inside it — so neither set blocks the other and no edge is written between them".

The first push under it, `0845841b`, annotated all 2,682 functions under `test/` and was rejected by all eleven workflows. The step reported 172 distinct errors and 138 of them were in `lib/python/` — `no-untyped-def` in `test_fixtures`, `module_utils` and `terraform_drift` — and three more in `scripts/`. The eleven steps could not go green on `test/` alone, so `#575` was in fact blocked by `#745`, `#746` and `#747`, which is the edge the issue said not to write. All four were done in one session and the eleven steps went green on `37b58407`.

## What this means for an issue about a flag

Before writing that a flag's scope is one directory, expand the closure rather than the argument list. `grep` the named paths for their imports, follow those into `lib/python/` and `scripts/`, and count the signatures the flag would refuse in everything it reaches. An issue that scopes a flag to the directory named on the command line understates the work by however much the closure adds, and the understatement surfaces as a rejected push rather than as a review comment.

Where the closure crosses into another issue's territory, that is a real `blocked_by` edge under the test in [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md): the issue in hand cannot be finished until the other one is.

## The same trap in the other direction

`--disallow-untyped-defs` is not on the eleven `mypy-source` commands yet — that is `#748` — but the annotations `#745`, `#746` and `#747` added put those bodies in front of `mypy-source` regardless, because `mypy` checks an annotated body whether or not the flag is set. Annotating a function is the thing that makes its body read; the flag only makes an unannotated one an error. So a commit that adds annotations can turn a green step red without touching a workflow file, and the step it turns red need not be the one the issue was about.

## Related notes

- [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md) — the four jobs each workflow carries and what each reads
- [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md) — why the shared library is named in every workflow's passes
- [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) — the test that decides whether a `blocked_by` edge is written
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — reading the whole failed step, and answering all of it in one follow-up
