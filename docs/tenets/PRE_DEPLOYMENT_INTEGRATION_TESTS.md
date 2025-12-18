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

## 2. Five-Layer Testing Model

Every resource dependency must be tested through five layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Authentication | Valid credentials exist | Can call sts:GetCallerIdentity |
| 2. Authorization | Permission to inspect resources | Can call s3:HeadBucket |
| 3. Existence | Resource actually exists | Bucket exists |
| 4. Configuration | Resource configured correctly | IAM role has required policy |
| 5. Capability | Can perform required operations | Can call s3:PutObject |

Each layer catches different failure modes:
- Layer 1 fails → credentials invalid or expired
- Layer 2 fails → credentials valid but lack permission to inspect
- Layer 3 fails → have permission to check, but resource doesn't exist
- Layer 4 fails → resource exists but misconfigured
- Layer 5 fails → resource exists and configured, but can't perform operations

## 3. Fail Fast with Granular Diagnostics

Cryptic errors like "AccessDenied: Access Denied" are unacceptable.

- Each test must be atomic: one assertion per test
- Tests must run in layer order (authentication before authorization before existence)
- When a test fails, the developer must know exactly where the chain broke
- Failure messages must include resource names and expected values

## 4. Test File Organization

Tests MUST be organized into exactly five files by layer:

```
test/api/endpoints/{endpoint}/pre_deployment/integration/
├── test_01_authentication.py  # Layer 1: Can authenticate to AWS
├── test_02_authorization.py   # Layer 2: Have permission to inspect prerequisites
├── test_03_existence.py       # Layer 3: Prerequisite resources exist
├── test_04_configuration.py   # Layer 4: Prerequisites configured correctly
└── test_05_capability.py      # Layer 5: Can perform required operations
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
    assert response is not None  # This fails if bucket doesn't exist - that's Layer 3
```

### Layer 3: Existence Tests (test_03_existence.py)

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

### Layer 4: Configuration Tests (test_04_configuration.py)

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

### Layer 5: Capability Tests (test_05_capability.py)

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
| IAM role exists | 3. Existence | test_03_existence.py |
| S3 bucket exists | 3. Existence | test_03_existence.py |
| API Gateway exists | 3. Existence | test_03_existence.py |
| Role has policy attached | 4. Configuration | test_04_configuration.py |
| Bucket has versioning | 4. Configuration | test_04_configuration.py |
| API has required resource | 4. Configuration | test_04_configuration.py |
| Can write to S3 | 5. Capability | test_05_capability.py |
| Can assume role | 5. Capability | test_05_capability.py |
| Can invoke Lambda | 5. Capability | test_05_capability.py |

## Workflow Reference

| Workflow | Prerequisites to Test | NOT Test (created by this workflow) |
|----------|----------------------|-------------------------------------|
| `endpoint_v1_runners` | IAM role from bootstrap, API Gateway from api_backend | SQS queues, DynamoDB tables, Lambda functions |
| `api_backend` | S3 buckets from bootstrap, Route53 zone | API Gateway, Lambda functions |
| `endpoint_v1_health` | API Gateway from api_backend | Lambda function |
| `image_for_ecs_runners` | ECR repository from bootstrap | Docker image |
