# Pre-Deployment Integration Tests Task List

This document outlines the tasks required to add pre-deployment integration tests to all workflows after bootstrap. The goal is to validate upstream dependencies exist and work properly before deploying infrastructure.

## Reference Implementation

The `endpoint_v1_image_for_ec2_runners_post` workflow already implements this pattern correctly:

- **Workflow:** `.github/workflows/endpoint_v1_image_for_ec2_runners_post.yml`
- **Test structure:** `test/api/endpoints/image_for_ec2_runners/post/pre_deployment/`
  - `__init__.py`
  - `unit/` - Pure unit tests (mocked AWS)
    - `__init__.py`
    - `conftest.py`
    - `test_*.py`
  - `integration/` - Real AWS calls to validate dependencies
    - `__init__.py`
    - `conftest.py`
    - `test_*.py`

---

## Workflow-Specific Tasks

### 1. www_shared

**Depends on:** bootstrap

- [x] Create directory structure:
  - [x] `test/www/shared/pre_deployment/unit/`
  - [x] `test/www/shared/pre_deployment/integration/`
- [x] Move existing tests from `test/www/shared/pre_deployment/` to `test/www/shared/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/www/shared/pre_deployment/conftest.py`
  - [x] `test/www/shared/pre_deployment/unit/conftest.py`
  - [x] `test/www/shared/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] Bootstrap S3 state bucket exists and is accessible
  - [x] Bootstrap IAM roles exist
  - [x] Route53 hosted zone exists
  - [x] Bootstrap terraform outputs are readable
- [x] Update `.github/workflows/www_shared.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies (infrastructure job needs pre-deployment integration)

---

### 2. api_backend

**Depends on:** www_shared

- [x] Create directory structure:
  - [x] `test/api/backend/pre_deployment/unit/`
  - [x] `test/api/backend/pre_deployment/integration/`
- [x] Move existing tests from `test/api/backend/pre_deployment/` to `test/api/backend/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/backend/pre_deployment/conftest.py`
  - [x] `test/api/backend/pre_deployment/unit/conftest.py`
  - [x] `test/api/backend/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] www_shared CloudFront distribution exists
  - [x] www_shared ACM certificate exists and is valid
  - [x] www_shared S3 bucket exists
  - [x] www_shared terraform outputs are readable
- [x] Update `.github/workflows/api_backend.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 3. endpoint_health

**Depends on:** api_backend

- [x] Create directory structure:
  - [x] `test/api/endpoints/health/pre_deployment/unit/`
  - [x] `test/api/endpoints/health/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/health/pre_deployment/` to `test/api/endpoints/health/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/health/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/health/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/health/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] api_backend API Gateway exists
  - [x] api_backend Lambda execution role exists
  - [x] api_backend terraform outputs are readable
- [x] Update `.github/workflows/endpoint_health.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 4. api_shared_ecr

**Depends on:** endpoint_health

- [x] Create directory structure:
  - [x] `test/api/shared/ecr/pre_deployment/unit/`
  - [x] `test/api/shared/ecr/pre_deployment/integration/`
- [x] Move existing tests from `test/api/shared/ecr/pre_deployment/` to `test/api/shared/ecr/pre_deployment/unit/` (if any exist)
- [x] Create conftest files:
  - [x] `test/api/shared/ecr/pre_deployment/conftest.py`
  - [x] `test/api/shared/ecr/pre_deployment/unit/conftest.py`
  - [x] `test/api/shared/ecr/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] endpoint_health Lambda is functional (returns 200)
  - [ ] IAM permissions for ECR operations exist
  - [x] endpoint_health terraform outputs are readable
- [x] Update `.github/workflows/api_shared_ecr.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 5. endpoint_v1_image_for_ecs_runners

**Depends on:** api_shared_ecr

- [x] Create directory structure:
  - [x] `test/api/endpoints/image_for_ecs_runners/pre_deployment/unit/`
  - [x] `test/api/endpoints/image_for_ecs_runners/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/image_for_ecs_runners/pre_deployment/` to `test/api/endpoints/image_for_ecs_runners/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/image_for_ecs_runners/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/image_for_ecs_runners/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/image_for_ecs_runners/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] ECR repository exists and is accessible
  - [x] ECR push permissions are valid
  - [ ] Base Docker image is pullable
  - [x] api_shared_ecr terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_image_for_ecs_runners.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 6. endpoint_v1_image_for_ec2_runners_post

**Depends on:** endpoint_health

- [x] Already has pre-deployment integration tests (reference implementation)
- [x] Verify conftest files exist at all levels:
  - [x] `test/api/endpoints/image_for_ec2_runners/post/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/image_for_ec2_runners/post/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/image_for_ec2_runners/post/pre_deployment/integration/conftest.py`

---

### 7. endpoint_v1_image_for_ec2_runners (endpoint)

**Depends on:** endpoint_v1_image_for_ec2_runners_post

- [x] Create directory structure:
  - [x] `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/unit/`
  - [x] `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/` to `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/image_for_ec2_runners/endpoint/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] At least one stable AMI exists
  - [x] AMI is in available state
  - [x] api_backend terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_image_for_ec2_runners.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 8. endpoint_v1_ecs_runner

**Depends on:** endpoint_v1_image_for_ecs_runners

- [x] Create directory structure:
  - [x] `test/api/endpoints/ecs_runner/pre_deployment/unit/`
  - [x] `test/api/endpoints/ecs_runner/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/ecs_runner/pre_deployment/` to `test/api/endpoints/ecs_runner/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/ecs_runner/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/ecs_runner/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/ecs_runner/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] At least one stable ECR image exists
  - [x] VPC and subnets exist
  - [x] Security groups exist
  - [x] endpoint_v1_image_for_ecs_runners terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_ecs_runner.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 9. endpoint_v1_ec2_runner

**Depends on:** endpoint_v1_image_for_ec2_runners

- [x] Create directory structure:
  - [x] `test/api/endpoints/ec2_runner/pre_deployment/unit/`
  - [x] `test/api/endpoints/ec2_runner/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/ec2_runner/pre_deployment/` to `test/api/endpoints/ec2_runner/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/ec2_runner/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/ec2_runner/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/ec2_runner/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] At least one stable AMI exists
  - [x] VPC and subnets exist
  - [x] Security groups exist
  - [x] endpoint_v1_image_for_ec2_runners terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_ec2_runner.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 10. endpoint_v1_runners

**Depends on:** endpoint_v1_ec2_runner, endpoint_v1_ecs_runner

- [x] Create directory structure:
  - [x] `test/api/endpoints/runners/pre_deployment/unit/`
  - [x] `test/api/endpoints/runners/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/runners/pre_deployment/` to `test/api/endpoints/runners/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/runners/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/runners/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/runners/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] EC2 runner endpoint exists and returns 200
  - [x] ECS runner endpoint exists and returns 200
  - [x] SQS queues exist
  - [x] DynamoDB tables exist
  - [x] Both runner endpoint terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_runners.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 11. endpoint_v1_echo

**Depends on:** endpoint_v1_ecs_runner

- [x] Create directory structure:
  - [x] `test/api/endpoints/echo/pre_deployment/unit/`
  - [x] `test/api/endpoints/echo/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/echo/pre_deployment/` to `test/api/endpoints/echo/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/echo/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/echo/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/echo/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] ECS runner infrastructure exists
  - [x] API Gateway exists
  - [x] Lambda execution role exists
  - [x] endpoint_v1_ecs_runner terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_echo.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 12. endpoint_v1_contact

**Depends on:** endpoint_v1_ecs_runner

- [x] Create directory structure:
  - [x] `test/api/endpoints/contact/pre_deployment/unit/`
  - [x] `test/api/endpoints/contact/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/contact/pre_deployment/` to `test/api/endpoints/contact/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/contact/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/contact/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/contact/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] ECS runner infrastructure exists
  - [x] API Gateway exists
  - [x] SES is configured
  - [x] endpoint_v1_ecs_runner terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_contact.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 13. endpoint_v1_rack_designer

**Depends on:** endpoint_v1_ecs_runner

- [x] Create directory structure:
  - [x] `test/api/endpoints/rack_designer/pre_deployment/unit/`
  - [x] `test/api/endpoints/rack_designer/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/rack_designer/pre_deployment/` to `test/api/endpoints/rack_designer/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/rack_designer/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/rack_designer/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/rack_designer/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] ECS runner infrastructure exists
  - [x] API Gateway exists
  - [x] S3 bucket for designs exists
  - [x] endpoint_v1_ecs_runner terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_rack_designer.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 14. endpoint_v1_simulation_soc

**Depends on:** endpoint_v1_ecs_runner

- [x] Create directory structure:
  - [x] `test/api/endpoints/simulation_soc/pre_deployment/unit/`
  - [x] `test/api/endpoints/simulation_soc/pre_deployment/integration/`
- [x] Move existing tests from `test/api/endpoints/simulation_soc/pre_deployment/` to `test/api/endpoints/simulation_soc/pre_deployment/unit/`
- [x] Create conftest files:
  - [x] `test/api/endpoints/simulation_soc/pre_deployment/conftest.py`
  - [x] `test/api/endpoints/simulation_soc/pre_deployment/unit/conftest.py`
  - [x] `test/api/endpoints/simulation_soc/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] ECS runner infrastructure exists
  - [x] API Gateway exists
  - [x] endpoint_v1_ecs_runner terraform outputs are readable
- [x] Update `.github/workflows/endpoint_v1_simulation_soc.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update `unit-testing` job to run `pre_deployment/unit/`
  - [x] Update job dependencies

---

### 15. www_index

**Depends on:** www_shared

- [x] Create directory structure:
  - [x] `test/www/index/pre_deployment/integration/`
- [x] Create conftest files:
  - [x] `test/www/index/pre_deployment/conftest.py`
  - [x] `test/www/index/pre_deployment/integration/conftest.py`
- [x] Create `__init__.py` files in new directories
- [x] Create pre-deployment integration tests to validate:
  - [x] S3 bucket for static files exists
  - [x] CloudFront distribution exists
  - [x] www_shared terraform outputs are readable
- [x] Update `.github/workflows/www_index.yml`:
  - [x] Add `integration-testing-pre-deployment` job
  - [x] Update job dependencies

---

## Rename Existing Post-Deployment Integration Test Jobs

Each workflow's existing "Integration testing" job runs post-deployment tests but its name doesn't clarify this. Rename both the job ID and display name to be explicit:

**Before:**
```yaml
  integration-testing:
    name: Integration testing
```

**After:**
```yaml
  integration-testing-post-deployment:
    name: Post-deployment integration testing
```

For each workflow, update:
- [x] `www_shared.yml` - already renamed `integration-testing` to `integration-testing-post-deployment`
- [x] `api_backend.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_health.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `api_shared_ecr.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_image_for_ecs_runners.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_image_for_ec2_runners.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_image_for_ec2_runners_post.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_ecs_runner.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_ec2_runner.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_runners.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_echo.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_contact.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_rack_designer.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `endpoint_v1_simulation_soc.yml` - rename `integration-testing` to `integration-testing-post-deployment`
- [x] `www_index.yml` - rename `integration-testing` to `integration-testing-post-deployment`

Also update any `needs:` references to this job in dependent jobs (e.g., `e2e-testing`).

---

## Pre-Deployment Integration Test Job Template

Add this job to each workflow YAML file (adjust paths and dependencies as needed):

```yaml
  integration-testing-pre-deployment:
    name: Pre-deployment integration testing
    needs:
      - declaring-common-variables
      - unit-testing
    permissions:
      contents: read
      id-token: write
    runs-on: >-
      ${{ ( vars.USE_GITHUB_HOSTED == 'true' ||
            github.event.inputs.github_hosted == 'true' ||
            contains(github.event.head_commit.message, '[github-hosted]') ||
            contains(github.event.workflow_run.head_commit.message,
              '[github-hosted]') ) &&
          'ubuntu-latest' ||
          fromJSON(format('["ecs", "fargate", "spot", "runner-{0}"]',
            github.run_id)) }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: >-
            ${{ needs.declaring-common-variables.outputs.tf_version }}
          terraform_wrapper: false
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-region: >-
            ${{ needs.declaring-common-variables.outputs.aws_region }}
          role-to-assume: >-
            ${{ needs.declaring-common-variables.outputs.role_arn }}
      - if: >-
          vars.USE_GITHUB_HOSTED == 'true' ||
          github.event.inputs.github_hosted == 'true' ||
          contains(github.event.head_commit.message, '[github-hosted]') ||
          contains(github.event.workflow_run.head_commit.message,
            '[github-hosted]')
        name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - if: >-
          vars.USE_GITHUB_HOSTED == 'true' ||
          github.event.inputs.github_hosted == 'true' ||
          contains(github.event.head_commit.message, '[github-hosted]') ||
          contains(github.event.workflow_run.head_commit.message,
            '[github-hosted]')
        name: Install Python dependencies
        run: python3 -m pip install boto3 botocore pytest pyyaml requests
      - name: Run pre-deployment integration tests
        run: |
          TEST_DIR=test/path/to/endpoint  # ADJUST THIS PATH
          python3 -m pytest $TEST_DIR/pre_deployment/integration/ \
            --confcutdir=$TEST_DIR --verbose --pythonwarnings=error
```

Update the `ensuring-endpoint-infrastructure-in-desired-state` job to depend on `integration-testing-pre-deployment`:

```yaml
  ensuring-endpoint-infrastructure-in-desired-state:
    needs:
      - declaring-common-variables
      - integration-testing-pre-deployment  # ADD THIS
      - unit-testing
```

---

## Conftest File Templates

### pre_deployment/conftest.py

```python
"""Pytest configuration for pre-deployment tests."""
```

### pre_deployment/unit/conftest.py

```python
"""Pytest fixtures for pre-deployment unit tests."""
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]  # Adjust depth as needed
SRC_DIR = REPO_ROOT / "src" / "path" / "to" / "endpoint"  # Adjust path


@pytest.fixture
def src_dir():
    """Provide the source directory path."""
    return SRC_DIR
```

### pre_deployment/integration/conftest.py

```python
"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]  # Adjust depth as needed
UPSTREAM_DIR = REPO_ROOT / "src" / "path" / "to" / "upstream"  # Adjust path


def _terraform_init(directory: Path) -> bool:
    """Initialize terraform in the given directory."""
    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def _terraform_output(directory: Path, name: str, as_json: bool = False) -> str:
    """Get a terraform output value."""
    cmd = ["terraform", "output", "-json" if as_json else "-raw", name]
    result = subprocess.run(
        cmd,
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return "us-east-1"  # Or read from config


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for upstream state access."""
    return _terraform_init(UPSTREAM_DIR)


@pytest.fixture(scope="session")
def upstream_outputs(terraform_initialized):
    """Get upstream terraform outputs."""
    if not terraform_initialized:
        return {}
    return {
        "example_output": _terraform_output(UPSTREAM_DIR, "example_output"),
    }
```

---

## Common Validation Patterns

### Validate S3 Bucket Exists

```python
def test_s3_bucket_exists(s3_client, bucket_name):
    """Verify the S3 bucket exists."""
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
```

### Validate IAM Role Exists

```python
def test_iam_role_exists(iam_client, role_name):
    """Verify the IAM role exists."""
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name
```

### Validate Terraform Output Readable

```python
def test_terraform_outputs_readable(upstream_outputs):
    """Verify upstream terraform outputs are accessible."""
    assert upstream_outputs.get("example_output"), "Missing example_output"
```

### Validate API Endpoint Responds

```python
def test_endpoint_responds(api_url, api_key):
    """Verify the API endpoint responds."""
    response = requests.get(
        f"{api_url}/health",
        headers={"x-api-key": api_key},
        timeout=10
    )
    assert response.status_code == 200
```

### Validate ECR Repository Exists

```python
def test_ecr_repository_exists(ecr_client, repository_name):
    """Verify the ECR repository exists."""
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1
```

### Validate VPC Resources Exist

```python
def test_vpc_exists(ec2_client, vpc_id):
    """Verify the VPC exists."""
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert len(response["Vpcs"]) == 1


def test_subnets_exist(ec2_client, subnet_ids):
    """Verify all subnets exist."""
    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert len(response["Subnets"]) == len(subnet_ids)


def test_security_group_exists(ec2_client, security_group_id):
    """Verify the security group exists."""
    response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
    assert len(response["SecurityGroups"]) == 1
```

---

## Execution Order

When implementing, follow the dependency graph order:

1. www_shared (depends on bootstrap)
2. api_backend (depends on www_shared)
3. endpoint_health (depends on api_backend)
4. api_shared_ecr (depends on endpoint_health)
5. endpoint_v1_image_for_ec2_runners_post (depends on endpoint_health) - already done
6. endpoint_v1_image_for_ecs_runners (depends on api_shared_ecr)
7. endpoint_v1_image_for_ec2_runners (depends on endpoint_v1_image_for_ec2_runners_post)
8. endpoint_v1_ecs_runner (depends on endpoint_v1_image_for_ecs_runners)
9. endpoint_v1_ec2_runner (depends on endpoint_v1_image_for_ec2_runners)
10. endpoint_v1_runners (depends on both runner endpoints)
11. endpoint_v1_echo (depends on endpoint_v1_ecs_runner)
12. endpoint_v1_contact (depends on endpoint_v1_ecs_runner)
13. endpoint_v1_rack_designer (depends on endpoint_v1_ecs_runner)
14. endpoint_v1_simulation_soc (depends on endpoint_v1_ecs_runner)
15. www_index (depends on endpoint_v1_contact)
