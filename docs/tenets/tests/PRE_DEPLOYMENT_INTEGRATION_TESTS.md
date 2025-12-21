# Pre-Deployment Integration Test Tenets

These are the non-negotiable rules for pre-deployment integration tests.

## 1. Only Test Prerequisites

**Pre-deployment tests ONLY test resources created by OTHER workflows that THIS workflow depends on.**

- Do test: Bootstrap resources that must exist before deployment
- Do test: IAM permissions required for deployment
- Do test: External resources referenced by terraform
- Do NOT test: Resources created by the deployment itself
- Do NOT test: Application logic or business rules
- Do NOT test: Things covered by unit tests

Resources created by the workflow don't exist yet when pre-deployment tests run. Testing for their existence will always fail.

Pre-deployment tests answer: "Can I deploy?"
Post-deployment tests answer: "Did deployment succeed?"

## 2. Six-Layer Testing Model

Every resource dependency must be tested through six layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Authentication | Valid credentials exist | Can call sts:GetCallerIdentity |
| 2. Authorization | Permission to inspect resources | Can call s3:HeadBucket |
| 3. State | Terraform state matches AWS reality | Resources to create don't already exist |
| 4. Existence | Resource actually exists | Bucket exists |
| 5. Configuration | Resource configured correctly | IAM role has required policy |
| 6. Capability | Can perform required operations | Can call s3:PutObject |

Each layer catches different failure modes:
- Layer 1 fails → credentials invalid or expired
- Layer 2 fails → credentials valid but lack permission to inspect
- Layer 3 fails → state drift - resources exist but not in Terraform state
- Layer 4 fails → have permission to check, but resource doesn't exist
- Layer 5 fails → resource exists but misconfigured
- Layer 6 fails → resource exists and configured, but can't perform operations

## 3. Fail Fast with Granular Diagnostics

Cryptic errors like "AccessDenied: Access Denied" are unacceptable.

- Each test must be atomic: one assertion per test
- Tests must run in layer order (authentication before authorization before state before existence)
- When a test fails, the developer must know exactly where the chain broke
- Failure messages must include resource names and expected values

## 4. Test File Organization

Tests MUST be organized into exactly six files by layer:

```
test/{module}/pre_deployment/integration/
├── test_01_authentication.py  # Layer 1: Can authenticate to AWS
├── test_02_authorization.py   # Layer 2: Have permission to inspect prerequisites
├── test_03_state.py           # Layer 3: Terraform state matches AWS reality
├── test_04_existence.py       # Layer 4: Prerequisite resources exist
├── test_05_configuration.py   # Layer 5: Prerequisites configured correctly
└── test_06_capability.py      # Layer 6: Can perform required operations
```

Do NOT organize by resource (test_s3.py, test_iam.py, test_dynamodb.py).
Organizing by resource makes it impossible to know which layer failed.

### Layer 1: Authentication Tests (test_01_authentication.py)

Test ONLY that credentials are valid. No authorization or resource checks.

```python
# CORRECT - authentication only
def test_aws_credentials_valid(sts_client):
    """Verify AWS credentials are valid."""
    response = sts_client.get_caller_identity()
    assert response["Account"] is not None

def test_aws_credentials_not_expired(sts_client):
    """Verify AWS credentials are not expired."""
    # get_caller_identity succeeds = credentials not expired
    response = sts_client.get_caller_identity()
    assert "Arn" in response
```

```python
# WRONG - mixing authentication with authorization
def test_aws_credentials_can_access_s3(s3_client):
    """Verify credentials can access S3."""
    response = s3_client.list_buckets()  # This is authorization, not authentication
    assert response is not None
```

### Layer 2: Authorization Tests (test_02_authorization.py)

Test that credentials have permission to INSPECT prerequisite resources. Not existence, not capability.

```python
# CORRECT - authorization to inspect only
def test_can_describe_iam_role(iam_client, config):
    """Verify permission to inspect IAM role."""
    try:
        iam_client.get_role(RoleName=config["github_actions_role_name"])
    except iam_client.exceptions.NoSuchEntityException:
        pass  # Role doesn't exist, but we have permission to check - that's OK here
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to inspect IAM role")
        raise

def test_can_describe_s3_bucket(s3_client, config):
    """Verify permission to inspect S3 bucket."""
    try:
        s3_client.head_bucket(Bucket=config["state_bucket_name"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "403":
            pytest.fail("No permission to inspect S3 bucket")
        # 404 means bucket doesn't exist - but we have permission to check
        if e.response["Error"]["Code"] != "404":
            raise
```

```python
# WRONG - checking existence in authorization test
def test_can_access_state_bucket(s3_client, config):
    """Verify can access state bucket."""
    response = s3_client.head_bucket(Bucket=config["state_bucket_name"])
    assert response is not None  # This fails if bucket doesn't exist - that's Layer 4
```

### Layer 3: State Tests (test_03_state.py)

Test that Terraform state matches AWS reality. Resources Terraform plans to create should not already exist. Uses `terraform_drift` from `lib/python/`.

```python
# CORRECT - state validation
from terraform_config import TEST_AWS_REGION
from terraform_drift import check_resource_exists, get_planned_creates

def test_no_orphaned_resources():
    """Verify resources to be created don't already exist in AWS."""
    creates = get_planned_creates(TERRAFORM_DIR)

    orphaned = []
    for resource in creates:
        if check_resource_exists(resource["type"], resource["name"], TEST_AWS_REGION):
            orphaned.append(resource)

    if orphaned:
        msg = "\nOrphaned resources detected:\n"
        for r in orphaned:
            msg += f"  - {r['type']}: {r['name']}\n"
            msg += f"    Fix: terraform import {r['address']} {r['name']}\n"
        pytest.fail(msg)
```

**Cold state exception:** For bootstrap workflows, skip state tests if no prior state exists:

```python
@pytest.mark.skipif(
    not _has_existing_state(),
    reason="Cold state - no prior Terraform state to validate against"
)
def test_no_orphaned_resources():
    ...
```

### Layer 4: Existence Tests (test_04_existence.py)

Test that prerequisite resources exist. Assumes authorization passed.

```python
# CORRECT - existence only
def test_github_actions_role_exists(iam_client, config):
    """Verify GitHub Actions IAM role exists."""
    response = iam_client.get_role(RoleName=config["github_actions_role_name"])
    assert response["Role"]["RoleName"] == config["github_actions_role_name"]

def test_state_bucket_exists(s3_client, config):
    """Verify Terraform state bucket exists."""
    response = s3_client.head_bucket(Bucket=config["state_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

def test_api_gateway_exists(apigateway_client, config):
    """Verify API Gateway exists."""
    response = apigateway_client.get_rest_api(restApiId=config["api_gateway_id"])
    assert response["id"] == config["api_gateway_id"]
```

```python
# WRONG - mixing existence with configuration
def test_github_actions_role_exists_with_correct_policy(iam_client, config):
    """Verify role exists with correct policy."""
    response = iam_client.get_role(RoleName=config["github_actions_role_name"])
    policies = iam_client.list_attached_role_policies(RoleName=config["github_actions_role_name"])
    assert len(policies["AttachedPolicies"]) > 0  # This is configuration, not existence
```

### Layer 5: Configuration Tests (test_05_configuration.py)

Test that prerequisite resources are configured correctly. Assumes existence passed.

```python
# CORRECT - configuration only
def test_github_actions_role_has_required_policy(iam_client, config):
    """Verify GitHub Actions role has required policy attached."""
    response = iam_client.list_attached_role_policies(
        RoleName=config["github_actions_role_name"]
    )
    policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
    assert config["required_policy_arn"] in policy_arns

def test_state_bucket_has_versioning_enabled(s3_client, config):
    """Verify state bucket has versioning enabled."""
    response = s3_client.get_bucket_versioning(Bucket=config["state_bucket_name"])
    assert response.get("Status") == "Enabled"

def test_api_gateway_has_runners_resource(apigateway_client, config):
    """Verify API Gateway has /v1/runners resource."""
    response = apigateway_client.get_resources(restApiId=config["api_gateway_id"])
    paths = [r["path"] for r in response["items"]]
    assert "/v1/runners" in paths
```

```python
# WRONG - re-checking existence in configuration test
def test_state_bucket_versioning(s3_client, config):
    """Verify state bucket versioning."""
    s3_client.head_bucket(Bucket=config["state_bucket_name"])  # existence check - unnecessary
    response = s3_client.get_bucket_versioning(Bucket=config["state_bucket_name"])
    assert response.get("Status") == "Enabled"
```

Use fixtures from existence tests. Don't re-verify existence.

### Layer 6: Capability Tests (test_06_capability.py)

Test that you can perform required operations. Assumes configuration passed.

```python
# CORRECT - capability with cleanup
def test_can_write_to_state_bucket(s3_client, config):
    """Verify can write to Terraform state bucket."""
    test_key = f"test/{uuid.uuid4()}.txt"
    try:
        s3_client.put_object(
            Bucket=config["state_bucket_name"],
            Key=test_key,
            Body=b"test"
        )
    finally:
        try:
            s3_client.delete_object(Bucket=config["state_bucket_name"], Key=test_key)
        except ClientError:
            pass

def test_can_assume_deployment_role(sts_client, config):
    """Verify can assume the deployment IAM role."""
    response = sts_client.assume_role(
        RoleArn=config["deployment_role_arn"],
        RoleSessionName="pre-deployment-test"
    )
    assert response["Credentials"]["AccessKeyId"] is not None
```

```python
# WRONG - no cleanup
def test_can_write_to_dynamodb(dynamodb_client, config):
    """Verify can write to DynamoDB."""
    dynamodb_client.put_item(
        TableName=config["table_name"],
        Item={"id": {"S": "test-item"}}
    )
    # Missing cleanup - test artifact remains!
```

**Always clean up in `finally` blocks.**

## 5. Cleanup After Capability Tests

If testing write operations, delete test artifacts in `finally` blocks.

```python
def test_can_write(client, resource_id):
    test_id = f"test-{uuid.uuid4()}"
    try:
        client.put_item(Id=test_id, Data="test")
    finally:
        try:
            client.delete_item(Id=test_id)
        except ClientError:
            pass
```

No test artifacts should remain after test execution.

## 6. Fixture Usage

Use fixtures to:
1. Create AWS clients once per module
2. Load configuration from shared config files
3. Cache resource identifiers discovered in earlier layers

```python
# conftest.py
@pytest.fixture(scope="module")
def sts_client(config):
    return boto3.client("sts", region_name=config["aws_region"])

@pytest.fixture(scope="module")
def iam_client(config):
    return boto3.client("iam", region_name=config["aws_region"])

@pytest.fixture(scope="module")
def config():
    """Load configuration from shared config file."""
    with open("etc/config.json") as f:
        return json.load(f)
```

## Quick Reference

| If you want to test... | Layer | File |
|------------------------|-------|------|
| AWS credentials valid | 1. Authentication | test_01_authentication.py |
| Can call sts:GetCallerIdentity | 1. Authentication | test_01_authentication.py |
| Can describe IAM role | 2. Authorization | test_02_authorization.py |
| Can head S3 bucket | 2. Authorization | test_02_authorization.py |
| Terraform state matches reality | 3. State | test_03_state.py |
| No orphaned resources | 3. State | test_03_state.py |
| IAM role exists | 4. Existence | test_04_existence.py |
| S3 bucket exists | 4. Existence | test_04_existence.py |
| API Gateway exists | 4. Existence | test_04_existence.py |
| Role has policy attached | 5. Configuration | test_05_configuration.py |
| Bucket has versioning | 5. Configuration | test_05_configuration.py |
| API has required resource | 5. Configuration | test_05_configuration.py |
| Can write to S3 | 6. Capability | test_06_capability.py |
| Can assume role | 6. Capability | test_06_capability.py |
| Can invoke Lambda | 6. Capability | test_06_capability.py |

## Workflow Reference

| Workflow | Prerequisites to Test | NOT Test (created by this workflow) |
|----------|----------------------|-------------------------------------|
| `endpoint_v1_runners` | IAM role from bootstrap, API Gateway from api_backend | SQS queues, DynamoDB tables, Lambda functions |
| `api_backend` | S3 buckets from bootstrap, Route53 zone | API Gateway, Lambda functions |
| `endpoint_v1_health` | API Gateway from api_backend | Lambda function |
| `image_for_ecs_runners` | ECR repository from bootstrap | Docker image |

## 8. Layer Marker Implementation

Tests use `pytest.mark.layer(N)` to enforce execution order. Layer N tests automatically skip if any test in layers 1 through N-1 failed.

### Usage

Apply the marker at the module level:

```python
# test_01_authentication.py
pytestmark = pytest.mark.layer(1)

# test_02_authorization.py
pytestmark = pytest.mark.layer(2)

# ... and so on for each layer
```

### How It Works

The layer system is implemented in `conftest.py` using three pytest hooks:

1. **`pytest_configure`** - Registers the `layer` marker
2. **`pytest_runtest_makereport`** - Tracks pass/fail counts per layer
3. **`pytest_runtest_setup`** - Skips tests if earlier layers failed

```python
# conftest.py implementation pattern
_layer_results: Dict[int, Dict[str, int]] = {}

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N"
    )

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    del call  # Required by hook signature but unused
    outcome = yield
    result = outcome.get_result()
    if result.when == "call":
        for marker in item.iter_markers("layer"):
            layer_num = marker.args[0]
            # Track pass/fail for this layer
            ...

def pytest_runtest_setup(item):
    for marker in item.iter_markers("layer"):
        layer_num = marker.args[0]
        for prev_layer in range(1, layer_num):
            if _layer_results.get(prev_layer, {}).get("failed", 0) > 0:
                pytest.skip(f"Skipped: layer {prev_layer} had failures")
```

## 9. Why Terraform Plan is Not a Workflow Step

Layer 3 (State) tests replace the need for a separate `terraform plan` step in workflows.

### What Layer 3 Does

- Uses `terraform_drift` library from `lib/python/`
- Runs `terraform plan` internally to detect planned creates
- Checks if those resources already exist in AWS
- Fails if orphaned resources detected (state drift)

### Why This is Better Than a Separate Plan Step

1. **Diagnostics**: Layer 3 tells you exactly which resources have drift
2. **Actionable**: Failure messages include `terraform import` commands
3. **Integrated**: Part of the test pyramid, not a separate manual step
4. **Granular**: Runs after authentication/authorization, so you know credentials work

If layer 3 passes, `terraform apply` will succeed (no unexpected resource conflicts).

## 10. Workflow Step Ordering

Pre-deployment integration tests require a specific position in the workflow:

```
1. Lint (pylint, mypy, yamllint, tflint)
2. Unit tests
3. Pre-deployment integration tests (layers 1-6)
4. Terraform apply
5. Post-deployment integration tests
6. E2E tests
```

### Why This Order

| Step | Depends On | Reason |
|------|------------|--------|
| Lint | Nothing | Fast feedback first |
| Unit tests | Lint | No point running tests if code has errors |
| Pre-deployment integration | Terraform init | Layer 3 needs state access |
| Terraform apply | Pre-deployment passing | Layer 3 validates no drift |
| Post-deployment integration | Resources exist | Can't test what doesn't exist |
| E2E tests | All above | Full system must be deployed |

### Key Points

- Pre-deployment tests run BEFORE `terraform apply`
- Layer 3 requires `terraform init` but NOT `terraform apply`
- If pre-deployment fails, skip apply (fail fast)
- Post-deployment and E2E tests run AFTER successful apply
