# A workflow lints and type-checks in four passes

## Table of Contents

- [The four passes](#the-four-passes)
- [Why source and tests are split](#why-source-and-tests-are-split)
- [Each pass reads its own subsystem](#each-pass-reads-its-own-subsystem)
- [The two subsystems that differ](#the-two-subsystems-that-differ)
- [What one of them looks like](#what-one-of-them-looks-like)
- [Related notes](#related-notes)

## The four passes

Every subsystem that has Python is linted and type-checked by its own workflow, in four passes: the linter over the source, the linter over the tests, the type checker over the source, the type checker over the tests. Each is a job of its own, so they run at once and a rejected push names all of them that failed rather than the first. Each carries the same step name in every workflow, which is what makes a red run readable without opening a log:

| Step name | What it reads |
| ----------- | --------------- |
| `Run pylint on source` | the workflow's own Lambda source directory, with the shared library on the import path |
| `Run pylint on tests` | the workflow's own test subtree, recursively, with the shared library and the scripts directory on the import path |
| `Run mypy on source` | the same source directory, with the shared library on the type path |
| `Run mypy on tests` | the same test subtree, with the shared library and the scripts directory on the type path |

Adding a subsystem means adding all four. A workflow with three of them has a half of one tool nobody is watching, and nothing else in the repository will notice.

## Why source and tests are split

The two halves need different settings. Tests import the shared library and the scripts directory and cannot resolve either without being told where they are, while source imports only the shared library; running the two together would mean giving the source pass a path it has no business seeing. The split also puts the answer in the job name: a failure says which half broke before anything is read.

## Each pass reads its own subsystem

A pass names what its own workflow's path filter names, and nothing else in the tree. That is what keeps a run a report on the subsystem the push touched — a workflow that widened its passes to the whole repository would fail on a file its own trigger does not watch, and would go red for a change it never saw.

The shared library is the case to be careful with. The test passes put it on the import path so the imports resolve, and that is all: it is on the path, not among the targets. It is read as code by the one workflow whose trigger names it, which owns it along with the scripts directory and the whole test tree and names all three across its four passes.

## The two subsystems that differ

A subsystem whose source is Terraform rather than Python carries the two test passes and omits the source ones, because there is no Python source to read. Bootstrap is the one that is like this.

The scripts workflow is the other, and is the exception described above: its source is the shared library and the scripts directory, so the thing every other workflow merely puts on a path is what this one lints.

## What one of them looks like

From the sessions endpoint's workflow, the whole of two of the four jobs:

```yaml
- name: Run pylint on source
  run: |
    SRC=src/api/endpoints/sessions
    PYTHONPATH=lib/python python3 -m pylint \
      $SRC/lambda/ \
      --fail-under=10.0
- name: Run pylint on tests
  run: |
    PYTHONPATH=lib/python:scripts python3 -m pylint \
      test/__init__.py \
      test/conftest.py \
      test/api/__init__.py \
      test/api/conftest.py \
      test/api/endpoints/__init__.py \
      test/api/endpoints/conftest.py \
      test/api/endpoints/sessions \
      --recursive=y \
      --fail-on=C,R,W --fail-under=10.0
```

The test pass lists the package and configuration files above its own subtree by name. Those files run in every suite below them, so a workflow that skipped them would leave the code its own tests are built on unread by anything.

## Related notes

Reading the result of these is [verification-in-ci-only](verification-in-ci-only.md), and answering a red one is [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
