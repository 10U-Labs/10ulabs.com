# A workflow lints and type-checks in four passes

## Table of Contents

- [The four passes](#the-four-passes)
- [Why source and tests are split](#why-source-and-tests-are-split)
- [Each pass reads its own subsystem](#each-pass-reads-its-own-subsystem)
- [The subsystem that differs](#the-subsystem-that-differs)
- [What one of them looks like](#what-one-of-them-looks-like)
- [Related notes](#related-notes)

## The four passes

Every subsystem that has Python is linted and type-checked by its own workflow, in four passes: the linter over the source, the linter over the tests, the type checker over the source, the type checker over the tests. Each is a job of its own, so they run at once and a rejected push names all of them that failed rather than the first. Each carries the same step name in every workflow, which is what makes a red run readable without opening a log:

| Step name | What it reads |
| ----------- | --------------- |
| `Run pylint on source` | the workflow's own Lambda source directory and the shared-library packages the workflow executes, with the shared library on the import path |
| `Run pylint on tests` | the workflow's own test subtree and the `test/lib/python/` suites covering the packages it executes, recursively, with the shared library and the scripts directory on the import path |
| `Run mypy on source` | the same targets, with the shared library on the type path |
| `Run mypy on tests` | the same targets, with the shared library and the scripts directory on the type path |

Adding a subsystem means adding all four. A workflow with three of them has a half of one tool nobody is watching, and nothing else in the repository will notice.

## Why source and tests are split

The two halves need different settings. Tests import the shared library and the scripts directory and cannot resolve either without being told where they are, while source imports only the shared library; running the two together would mean giving the source pass a path it has no business seeing. The split also puts the answer in the job name: a failure says which half broke before anything is read.

## Each pass reads its own subsystem

A pass names what its own workflow's path filter names, and nothing else in the tree. That is what keeps a run a report on the subsystem the push touched — a workflow that widened its passes to the whole repository would fail on a file its own trigger does not watch, and would go red for a change it never saw.

The shared library is inside that sentence rather than an exception to it. A workflow's `paths` filter names every `lib/python/` package the workflow executes and every `test/lib/python/` suite covering one, so those packages are its own subsystem too and its passes name them: the source passes read the packages, the test passes read the suites. The filter and the argument lists carry the same set, which is the check to run when either is edited. That rule is [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md), which also has the history of what happened when one workflow read the library for everybody.

## The subsystem that differs

A subsystem whose source is Terraform rather than Python still carries all four passes. There is no Lambda source directory for the source passes to name, and what they name instead is the shared-library packages the workflow executes — bootstrap is like this, and its `Run pylint on source` step is a list of `lib/python/` packages and nothing else.

The scripts workflow is the one that differs. It deploys nothing, so it has no subsystem directory under `src/` and no deployment job, and its source passes read `scripts/` — the one program the deploys shell out to. `39e1ad90` scoped it to that under `#607`; before then it was also the one workflow reading the shared library, which is the arrangement the rule linked above replaced.

## What one of them looks like

From the sessions endpoint's workflow, the whole of two of the four jobs:

```yaml
  pylint-source:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install Python dependencies
        run: |
          python3 -m pip install \
            boto3 \
            botocore \
            pylint \
            pytest \
            requests
      - name: Run pylint on source
        run: |
          SRC=src/api/endpoints/sessions
          PYTHONPATH=lib/python python3 -m pylint \
            $SRC/lambda/ \
            lib/python/boto_mocks \
            lib/python/lambda_response \
            lib/python/module_utils \
            lib/python/naming_conventions \
            lib/python/repo_utils \
            lib/python/terraform_config \
            lib/python/test_fixtures \
            --recursive=y \
            --disable=missing-module-docstring \
            --disable=missing-class-docstring \
            --disable=missing-function-docstring \
            --fail-on=C,R,W --fail-under=10.0
  pylint-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install Python dependencies
        run: |
          python3 -m pip install \
            boto3 \
            botocore \
            pylint \
            pytest \
            'python-hcl2<8' \
            requests
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
            test/lib/__init__.py \
            test/lib/python/__init__.py \
            test/lib/python/test_boto_mocks \
            test/lib/python/test_lambda_response \
            test/lib/python/test_module_utils \
            test/lib/python/test_naming_conventions \
            test/lib/python/test_naming_conventions_helpers \
            test/lib/python/test_repo_utils \
            test/lib/python/test_terraform_config \
            test/lib/python/test_test_fixtures \
            --recursive=y \
            --disable=missing-module-docstring \
            --disable=missing-class-docstring \
            --disable=missing-function-docstring \
            --fail-on=C,R,W --fail-under=10.0
```

Three kinds of path are in those lists. The source pass names the workflow's own Lambda directory and then the seven shared-library packages this endpoint executes. The test pass names the package and configuration files above its own subtree by name — those run in every suite below them, so a workflow that skipped them would leave the code its own tests are built on unread by anything — then its own subtree, then the `test/lib/python/` suite for each of those seven packages.

The three steps before the pylint step in each job are where the split of "Why source and tests are split" is visible. `pylint-tests` installs `'python-hcl2<8'` and `pylint-source` does not: the endpoint's own unit subtree has a test that parses its Terraform, and no file the source pass reads imports the parser. That is the same asymmetry as the import path, which `pylint-tests` sets to `lib/python:scripts` and `pylint-source` to `lib/python` alone. The three `--disable=missing-*-docstring` lines are the other half of a rule stated elsewhere: `assert-no-comments` refuses a docstring anywhere in the tree, and those lines are what stops the four passes demanding back what it refuses. A copy of these jobs written without them goes red on every file it reads.

## Related notes

What the four passes read beyond the workflow's own directories is [a-workflow-reads-the-library-it-executes](a-workflow-reads-the-library-it-executes.md). Reading the result of these is [verification-in-ci-only](verification-in-ci-only.md), and answering a red one is [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
