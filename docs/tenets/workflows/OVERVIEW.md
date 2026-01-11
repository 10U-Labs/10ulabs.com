# Workflow Tenets

This document defines the standard patterns for GitHub Actions workflows in this
repository. The reference implementation is:

- `api_endpoint_v1_github_workflows_webhooks.yml`

## 1. Step Ordering

Steps must follow this order:

1. Checkout code
2. Verify OIDC variables
3. Configure AWS credentials via OIDC
4. Set up Python (conditional on GitHub-hosted)
5. Install Python dependencies (conditional on GitHub-hosted)
6. Assert no linter config files
7. Assert no inline lint disables
8. Assert one assert per pytest
9. Linting YAML files
10. Run pylint on source
11. Run pylint on tests
12. Run mypy on source
13. Run mypy on tests
14. Install jscpd (conditional on GitHub-hosted)
15. Check for duplicate code in source Python files
16. Check for duplicate code in test Python files
17. Extract Terraform version (conditional on GitHub-hosted)
18. Setup Terraform (conditional on GitHub-hosted)
19. Terraform Format Check
20. Terraform Init
21. Setup TFLint (conditional on GitHub-hosted)
22. Run tflint
23. Run unit tests
24. Run pre-deployment integration tests
25. Terraform Plan
26. Terraform Apply
27. Run post-deployment integration tests
28. Run E2E tests
29. Dispatch descendant workflows (conditional)

For workflows without source Python files (e.g., infrastructure-only workflows),
omit source steps (10, 12, 15).

## 2. Assertion Steps

Three assertion steps must run before any linting:

```yaml
- name: Assert no linter config files
  run: >-
    assert-no-linter-config-files
    --linters pylint,mypy,yamllint
    --verbose
    ${{ github.workspace }}

- name: Assert no inline lint disables
  run: >-
    assert-no-inline-directives
    --tools pylint,mypy,yamllint
    --verbose
    ${{ github.workspace }}/**/*

- name: Assert one assert per pytest
  run: >-
    assert-one-assert-per-pytest
    --verbose
    ${{ github.workspace }}/test
```

These require installing the assertion tools in the Python dependencies step:

```yaml
python3 -m pip install \
  assert-no-inline-directives \
  assert-no-linter-config-files \
  assert-one-assert-per-pytest \
  ...
```

## 3. Pylint Separation: Source vs Tests

Pylint must run in two separate steps when source code exists:

```yaml
- name: Run pylint on source
  run: |
    SRC=src/api/endpoints/your_endpoint
    python3 -m pylint lib/python/ $SRC/lambdas/ --fail-under=10.0

- name: Run pylint on tests
  run: |
    TEST=test/api/endpoints/your_endpoint
    PYTHONPATH=lib/python:. python3 -m pylint \
      lib/python/ $TEST/ \
      --fail-on=C,R,W --fail-under=10.0
```

Key points:

- Source step runs without `PYTHONPATH` prefix
- Test step requires `PYTHONPATH=lib/python:.` prefix
- Both include `lib/python/` in the targets
- Test step targets the workflow-specific test directory
- Source uses `--fail-under=10.0` only
- Test uses `--fail-on=C,R,W --fail-under=10.0`

## 4. Mypy Separation: Source vs Tests

Mypy must run in two separate steps when source code exists:

```yaml
- name: Run mypy on source
  run: |
    SRC=src/api/endpoints/your_endpoint
    python3 -m mypy lib/python/ $SRC/lambdas/

- name: Run mypy on tests
  run: |
    TEST=test/api/endpoints/your_endpoint
    MYPYPATH=lib/python
    MYPYPATH=$MYPYPATH:src/api/endpoints/other/lambda  # Add as needed
    MYPYPATH=$MYPYPATH python3 -m mypy lib/python/ $TEST/
```

Key points:

- Source step runs without `MYPYPATH` prefix
- Test step requires `MYPYPATH=lib/python` prefix
- Add additional paths to MYPYPATH as needed for test imports
- Both include `lib/python/` in the targets
- Test step targets the workflow-specific test directory

## 5. Duplicate Code Checking (jscpd)

Duplicate code detection must run in two separate steps when source code exists:

```yaml
- name: Check for duplicate code in source Python files
  run: |
    SRC=src/api/endpoints/your_endpoint
    jscpd --pattern "**/*.py" --threshold 0 --reporters console \
      lib/python/ $SRC/lambdas/

- name: Check for duplicate code in test Python files
  run: |
    jscpd --pattern "**/*.py" --threshold 0 --reporters console \
      lib/python/ test/api/endpoints/your_endpoint/
```

Key points:

- Threshold is always 0 (no duplicates allowed)
- Both include `lib/python/` in the targets
- Test step targets the workflow-specific test directory

## 6. Conditional Installation for GitHub-Hosted vs ECS Runners

Tool installation steps must be conditional on GitHub-hosted runners:

```yaml
if: >-
  vars.WORKFLOWS_MUST_USE_GITHUB_HOSTED_RUNNERS == 'true' ||
  github.event.inputs.github_hosted == 'true' ||
  contains(github.event.head_commit.message, '[github-hosted]')
```

This applies to:

- Set up Python
- Install Python dependencies
- Install jscpd
- Extract Terraform version
- Setup Terraform
- Setup TFLint

The actual usage steps (assertions, linting, testing) run unconditionally on all
runners since ECS runners have these tools pre-installed.

## 7. Batched Dependency Installation

All Python dependencies must be installed in a single `pip install` command:

```yaml
- if: [GITHUB_HOSTED_CONDITION]
  name: Install Python dependencies
  run: |
    python3 -m pip install \
      assert-no-inline-directives \
      assert-no-linter-config-files \
      assert-one-assert-per-pytest \
      boto3 \
      boto3-stubs \
      botocore \
      dnspython \
      mypy \
      pylint \
      pytest \
      python-hcl2 \
      requests \
      types-PyYAML \
      types-requests \
      yamllint
```

## 8. Test Execution Ordering

Tests must follow the testing pyramid and deployment lifecycle:

```yaml
# Pre-deployment
- name: Run unit tests
  run: |
    TEST=test/api/endpoints/your_endpoint
    PYTHONPATH=lib/python python3 -m pytest \
      $TEST/pre_deployment/unit/ \
      --confcutdir=test --verbose --pythonwarnings=error

- name: Run pre-deployment integration tests
  run: |
    BASE=test/api/endpoints/your_endpoint
    PYTHONPATH=lib/python python3 -m pytest \
      $BASE/pre_deployment/integration/ \
      --capture=no --confcutdir=test --verbose --pythonwarnings=error

# Deploy
- name: Terraform Plan
  run: |
    cd src/api/endpoints/your_endpoint && \
      terraform plan

- name: Terraform Apply
  run: |
    cd src/api/endpoints/your_endpoint && \
      terraform apply -auto-approve

# Post-deployment
- name: Run post-deployment integration tests
  run: |
    BASE=test/api/endpoints/your_endpoint
    PYTHONPATH=lib/python python3 -m pytest \
      $BASE/post_deployment/integration/ \
      --confcutdir=test --verbose --pythonwarnings=error

- name: Run E2E tests
  run: |
    BASE=test/api/endpoints/your_endpoint
    PYTHONPATH=lib/python python3 -m pytest \
      $BASE/post_deployment/e2e/ \
      --confcutdir=test --verbose --pythonwarnings=error
```

Key points:

- All pytest commands use `--confcutdir=test --verbose --pythonwarnings=error`
- Pre-deployment integration tests add `--capture=no`
- Tests target workflow-specific directories

## 9. Terraform Workflow Order

Terraform steps must follow this order:

1. **Terraform Format Check** - `terraform fmt -diff -check -recursive`
2. **Terraform Init** - `terraform init`
3. **Run tflint** - `tflint --init && tflint`
4. [Unit tests, pre-deployment integration tests...]
5. **Terraform Plan** - `terraform plan`
6. **Terraform Apply** - `terraform apply -auto-approve`
7. [Post-deployment integration tests, E2E tests...]

## 10. Step Naming Conventions

Use these exact step names for consistency:

| Step | Name |
|------|------|
| Checkout | `Checkout code` |
| OIDC verify | `Verify OIDC variables` |
| AWS credentials | `Configure AWS credentials via OIDC` |
| Python setup | `Set up Python` |
| Python deps | `Install Python dependencies` |
| Assert config | `Assert no linter config files` |
| Assert inline | `Assert no inline lint disables` |
| Assert pytest | `Assert one assert per pytest` |
| YAML lint | `Linting YAML files` |
| Pylint source | `Run pylint on source` |
| Pylint tests | `Run pylint on tests` |
| Mypy source | `Run mypy on source` |
| Mypy tests | `Run mypy on tests` |
| jscpd install | `Install jscpd` |
| jscpd source | `Check for duplicate code in source Python files` |
| jscpd tests | `Check for duplicate code in test Python files` |
| TF version | `Extract Terraform version` |
| TF setup | `Setup Terraform` |
| TF format | `Terraform Format Check` |
| TF init | `Terraform Init` |
| TFLint setup | `Setup TFLint` |
| TFLint run | `Run tflint` |
| Unit tests | `Run unit tests` |
| Pre-deploy integration | `Run pre-deployment integration tests` |
| TF plan | `Terraform Plan` |
| TF apply | `Terraform Apply` |
| Post-deploy integration | `Run post-deployment integration tests` |
| E2E tests | `Run E2E tests` |
| Dispatch | `Dispatch descendant workflows` |

## 11. Fail-Fast Behavior

Workflows use fail-fast behavior - no `continue-on-error`. If a step fails, the
workflow stops immediately. This provides faster feedback and clearer error
messages.

## 12. Descendant Workflow Dispatch

Workflows that have dependents should include a conditional dispatch step:

```yaml
- env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  if: >-
    github.event_name == 'workflow_dispatch' &&
    (
    github.event.inputs.trigger_descendants == 'true' ||
     contains(github.event.head_commit.message,
     '[trigger descendants]'))
  name: Dispatch descendant workflows
  run: |
    FLAGS=""
    TRIGGER="${{ github.event.inputs.trigger_descendants }}"
    INVALIDATE="${{ github.event.inputs.invalidate_cloudfront }}"
    if [ "$TRIGGER" = "true" ]; then
      FLAGS="$FLAGS --trigger-descendants"
    fi
    if [ "$INVALIDATE" = "true" ]; then
      FLAGS="$FLAGS --invalidate-cloudfront"
    fi
    python3 src/workflowctl/workflowctl.py dispatch-descendant-workflows \
      --workflow your_workflow_name \
      --repo ${{ github.repository }} \
      $FLAGS
```

## 13. Workflow Inputs

Standard workflow inputs:

```yaml
on:
  workflow_dispatch:
    inputs:
      github_hosted:
        default: false
        description: 'Use GitHub-hosted runner instead of ephemeral ECS'
        type: boolean
      invalidate_cloudfront:
        default: false
        description: Force CloudFront cache invalidation
        type: boolean
      spot_recovery_reason:
        description: Spot recovery trigger reason
        required: false
        type: string
      trigger_descendants:
        default: false
        description: Trigger descendant workflows after this workflow completes
        type: boolean
```

## 14. Runner Selection

Use this pattern for runner selection to support both GitHub-hosted and ECS runners:

```yaml
runs-on: >-
  ${{ ( vars.WORKFLOWS_MUST_USE_GITHUB_HOSTED_RUNNERS == 'true' ||
        github.event.inputs.github_hosted == 'true' ||
        contains(github.event.head_commit.message, '[github-hosted]') ) &&
      'ubuntu-latest' ||
      fromJSON(format('["ecs", "fargate", "arm", "spot", "runner-{0}"]',
        github.run_id)) }}
```

## 15. Concurrency Control

All workflows must include concurrency settings:

```yaml
concurrency:
  cancel-in-progress: true
  group: ${{ github.workflow_ref }}-${{ github.ref }}
```

## 16. Permissions

Standard permissions for deploy jobs:

```yaml
permissions:
  actions: write
  contents: read
  id-token: write
```

## 17. Deploy Condition

Deploy jobs should only run on main branch:

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
```
