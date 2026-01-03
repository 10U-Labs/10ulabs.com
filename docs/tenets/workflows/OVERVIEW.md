# Workflow Tenets

This document defines the standard patterns for GitHub Actions workflows in this
repository. These patterns are derived from the following reference workflows:

- `bootstrap.yml`
- `www_common.yml`
- `api_common_routing.yml`
- `api_operational_health.yml`
- `api_common_networking.yml`

## 1. Static Analysis Step Ordering

Static analysis steps must follow this order:

1. Terraform Format Check
2. Terraform Init
3. Run tflint
4. Linting YAML files
5. Run pylint on source
6. Run pylint on tests
7. Run mypy on source
8. Run mypy on tests
9. Check for duplicate code in source Python files
10. Check for duplicate code in test Python files

For workflows without source Python files (e.g., infrastructure-only workflows like
`www_common.yml`), omit source steps (5, 7, 9). See sections 2-4 for details.

## 2. Pylint Separation: Source vs Tests

Pylint must run in two separate steps when source code exists:

```yaml
- name: Run pylint on source
  run: |
    python3 -m pylint lib/python/ src/path/to/handler.py \
      --fail-on=C,R,W --fail-under=10.0

- name: Run pylint on tests
  run: |
    PYTHONPATH=lib/python python3 -m pylint \
      lib/python/ test/ \
      --fail-on=C,R,W --fail-under=10.0
```

For workflows without source Python files (e.g., infrastructure-only workflows like
`www_common.yml`), use only the test step:

```yaml
- name: Run pylint on tests
  run: |
    PYTHONPATH=lib/python python3 -m pylint \
      lib/python/ test/ \
      --fail-on=C,R,W --fail-under=10.0
```

Key points:

- Source step runs without `PYTHONPATH` prefix
- Test step requires `PYTHONPATH=lib/python` prefix
- Both include `lib/python/` in the targets
- Test step targets the full `test/` directory, not workflow-specific subdirectories
- Both use `--fail-on=C,R,W --fail-under=10.0`
- Skip the source step when the only Python source is `lib/python/` (already covered by
  test step)

## 3. Mypy Separation: Source vs Tests

Mypy must run in two separate steps when source code exists:

```yaml
- name: Run mypy on source
  run: |
    python3 -m mypy lib/python/ src/path/to/handler.py

- name: Run mypy on tests
  run: |
    MYPYPATH=lib/python python3 -m mypy \
      lib/python/ test/
```

For workflows without source Python files (e.g., infrastructure-only workflows like
`www_common.yml`), use only the test step:

```yaml
- name: Run mypy on tests
  run: MYPYPATH=lib/python python3 -m mypy lib/python/ test/
```

Key points:

- Source step runs without `MYPYPATH` prefix
- Test step requires `MYPYPATH=lib/python` prefix
- Both include `lib/python/` in the targets
- Test step targets the full `test/` directory, not workflow-specific subdirectories
- Skip the source step when the only Python source is `lib/python/` (already covered by
  test step)

## 4. Duplicate Code Checking (jscpd)

Duplicate code detection must run in two separate steps when source code exists:

```yaml
- name: Check for duplicate code in source Python files
  run: |
    jscpd --pattern "**/*.py" --threshold 0 --reporters console \
      lib/python/ src/path/to/lambda/

- name: Check for duplicate code in test Python files
  run: |
    jscpd --pattern "**/*.py" --threshold 0 --reporters console \
      lib/python/ test/
```

For workflows without source Python files (e.g., infrastructure-only workflows like
`www_common.yml`), use only the test step:

```yaml
- name: Check for duplicate code in test Python files
  run: |
    jscpd --pattern "**/*.py" --threshold 0 --reporters console \
      lib/python/ test/
```

Key points:

- Threshold is always 0 (no duplicates allowed)
- Both include `lib/python/` in the targets
- Test step targets the full `test/` directory, not workflow-specific subdirectories
- Skip the source step when the only Python source is `lib/python/` (already covered by
  test step)

## 5. Batched Dependency Installation

All tool installations must happen at the start of the workflow, immediately after
Checkout and assertion steps. This ensures linting and tests can run even if
credentials or Terraform init fails (due to `continue-on-error: true`).

```yaml
# After Checkout and assertion steps, install all tools:
- if: [GITHUB_HOSTED_CONDITION]
  name: Setup Terraform
  uses: hashicorp/setup-terraform@v3
  with:
    terraform_version: ${{ steps.terraform.outputs.version }}
- if: [GITHUB_HOSTED_CONDITION]
  name: Setup TFLint
  uses: terraform-linters/setup-tflint@v6
- if: [GITHUB_HOSTED_CONDITION]
  name: Set up Python
  uses: actions/setup-python@v5
- if: [GITHUB_HOSTED_CONDITION]
  name: Install yamllint
  run: python3 -m pip install yamllint
- if: [GITHUB_HOSTED_CONDITION]
  name: Install pylint
  run: python3 -m pip install pylint ...
- if: [GITHUB_HOSTED_CONDITION]
  name: Install mypy
  run: python3 -m pip install mypy boto3-stubs types-requests
- if: [GITHUB_HOSTED_CONDITION]
  name: Install jscpd
  run: npm install -g jscpd
- if: [GITHUB_HOSTED_CONDITION]
  name: Install pytest dependencies
  run: python3 -m pip install pytest ...

# Then run checks, credentials, and tests
```

Batching installations at the start enables all independent checks to run regardless
of failures in credential or infrastructure steps.

## 6. Conditional Installation for GitHub-Hosted vs ECS Runners

Tool installation steps must be conditional on GitHub-hosted runners:

```yaml
if: >-
  vars.USE_GITHUB_HOSTED == 'true' ||
  github.event.inputs.github_hosted == 'true' ||
  contains(github.event.head_commit.message, '[github-hosted]')
```

This applies to:

- Setup Terraform
- Set up Python
- Install yamllint
- Install pylint
- Install mypy
- Install jscpd
- Install pytest dependencies

The actual usage steps (linting, testing) run unconditionally on all runners.

## 7. Test Execution Ordering

Tests must follow the testing pyramid and deployment lifecycle:

```yaml
# Pre-deployment
- name: Run unit tests
  run: python3 -m pytest test/path/pre_deployment/unit/ ...

- name: Run pre-deployment integration tests
  run: python3 -m pytest test/path/pre_deployment/integration/ ...

# Deploy
- name: Terraform Apply
  run: cd src/path && terraform apply -auto-approve

# Post-deployment
- name: Run post-deployment integration tests
  run: python3 -m pytest test/path/post_deployment/integration/ ...

- name: Run E2E tests
  run: python3 -m pytest test/path/post_deployment/e2e/ ...
```

## 8. Terraform Workflow Order

Terraform steps must follow this order:

1. **Terraform Format Check** - `terraform fmt -diff -check -recursive`
2. **Terraform Init** - `terraform init`
3. **Run tflint** - `tflint --init && tflint`
4. [Static analysis and tests...]
5. **Terraform Apply** - `terraform apply -auto-approve`

## 9. Step Naming Conventions

Use these exact step names for consistency:

| Step | Name |
|------|------|
| Terraform format | `Terraform Format Check` |
| Terraform init | `Terraform Init` |
| TFLint setup | `Setup TFLint` |
| TFLint run | `Run tflint` |
| Python setup | `Set up Python` |
| YAML lint install | `Install yamllint` |
| YAML lint run | `Linting YAML files` |
| Pylint install | `Install pylint` |
| Pylint source | `Run pylint on source` |
| Pylint tests | `Run pylint on tests` |
| Mypy install | `Install mypy` |
| Mypy source | `Run mypy on source` |
| Mypy tests | `Run mypy on tests` |
| jscpd install | `Install jscpd` |
| jscpd source | `Check for duplicate code in source Python files` |
| jscpd tests | `Check for duplicate code in test Python files` |
| Pytest install | `Install pytest dependencies` |
| Unit tests | `Run unit tests` |
| Pre-deploy integration | `Run pre-deployment integration tests` |
| Terraform apply | `Terraform Apply` |
| Post-deploy integration | `Run post-deployment integration tests` |
| E2E tests | `Run E2E tests` |

## 10. Continue-On-Error Pattern

All check and test steps must use `continue-on-error: true` so that failures don't
prevent subsequent steps from running. This ensures all issues are reported in a
single workflow run.

### Required Step Attributes

Every check/test step needs:

- `continue-on-error: true`
- `id: step_name` (snake_case identifier)

Example:

```yaml
- continue-on-error: true
  id: pylint
  name: Run pylint on tests
  run: ...

- continue-on-error: true
  id: unit_tests
  name: Run unit tests
  run: ...
```

### Final Assertion Step

Add an "Assert no step failed" step at the end that checks all outcomes:

```yaml
- env:
    PYLINT: ${{ steps.pylint.outcome }}
    UNIT_TESTS: ${{ steps.unit_tests.outcome }}
    # ... all other step outcomes
  name: Assert no step failed
  run: |
    failed=""
    [ "$PYLINT" = "failure" ] && failed="$failed pylint"
    [ "$UNIT_TESTS" = "failure" ] && failed="$failed unit_tests"
    # ... check all steps
    if [ -n "$failed" ]; then
      echo "Steps that failed:$failed"
      exit 1
    fi
    echo "All steps succeeded"
```

### Which Steps Get continue-on-error

| Step Type                          | continue-on-error |
|------------------------------------|-------------------|
| Checkout, Setup, Install           | No                |
| AWS credentials, Terraform Init    | Yes               |
| Linting (yamllint, pylint, mypy)   | Yes               |
| Duplicate code check (jscpd)       | Yes               |
| Tests (unit, integration, e2e)     | Yes               |
| Terraform Apply                    | Yes               |
| Assert no step failed              | No (final gate)   |

Steps like linting and unit tests don't depend on AWS credentials or Terraform Init
succeeding, so those infrastructure steps should also use `continue-on-error: true`
to allow independent steps to run.
