# Approach to Pre-Deployment Integration Tests

Pre-deployment integration tests validate that infrastructure dependencies exist and are properly configured **before** attempting deployment. This catches misconfigurations early with precise diagnostic information.

## Philosophy: Fail Fast with Granular Diagnostics

When a deployment fails, the error message is often cryptic:

```
Error: AccessDenied: Access Denied
```

This tells you nothing about *why* access was denied. Was the resource missing? Did the role exist but lack permissions? Did the policy exist but an SCP block the action? Were credentials even configured?

Our approach uses a **battery of atomic tests** ordered by dependency. When a test fails, you know exactly where the chain broke.

## Five-Layer Testing Model

Each resource dependency is tested through five layers, in order:

### Layer 1: Authentication
Do we have valid credentials to talk to AWS at all?

```
Test: Are AWS credentials configured?
Pass: Credentials found, continue testing
Fail: "No AWS credentials found. Configure via environment, ~/.aws/credentials, or IAM role."

Test: Can we call sts:GetCallerIdentity?
Pass: API call succeeded, continue testing
Fail: "Credentials invalid or expired."
```

### Layer 2: Authorization
Do we have permission to even check if resources exist?

```
Test: Can we call s3:HeadBucket?
Pass: API permission granted, continue testing
Fail: "No permission to call HeadBucket. Check IAM policy."
```

### Layer 3: Existence
Does the resource actually exist?

```
Test: Does the S3 bucket exist?
Pass: Bucket exists, continue testing
Fail: "Bucket 'X' does not exist. Run terraform apply in src/bootstrap/"
```

### Layer 4: Configuration
Is the resource configured correctly?

```
Test: Does the IAM role have AdministratorAccess policy attached?
Pass: Policy attached, continue testing
Fail: "Role missing AdministratorAccess policy. Attached policies: [...]"
```

### Layer 5: Capability
Can we actually perform the operations deployment requires?

```
Test: Can we call s3:PutObject?
Pass: Write succeeded
Fail: "No permission to write to bucket. SCP or bucket policy may be blocking."
```

## Why Five Layers?

Each layer catches different failure modes:

| Layer | Catches |
|-------|---------|
| Authentication | Missing credentials, expired tokens, misconfigured OIDC |
| Authorization | Missing IAM permissions to inspect resources |
| Existence | Deleted resources, wrong account, typos in resource names |
| Configuration | Misconfigured policies, missing attachments, wrong settings |
| Capability | SCPs blocking actions, bucket policies denying access, resource policies |

When Layer 3 fails but Layers 1-2 pass, you know:
- Credentials are valid
- You have permission to check if the bucket exists
- The bucket itself doesn't exist

When Layer 5 fails but Layers 1-4 pass, you know:
- Everything looks correct
- Something external (SCP, bucket policy, resource policy) is blocking the action

This precision eliminates guesswork.

## Diagnostic Chain Example

Consider S3 state bucket access. The test battery runs in order:

| Order | Layer | Test | Failure Meaning |
|-------|-------|------|-----------------|
| 1 | Authentication | Credentials available | No AWS credentials configured |
| 2 | Authentication | Can call STS API | Credentials invalid or expired |
| 3 | Authorization | Can call HeadBucket API | No permission to check bucket existence |
| 4 | Existence | Bucket exists | Bucket deleted or never created |
| 5 | Capability | Can list objects | Can check bucket but can't list contents |
| 6 | Capability | Can get object | Can list but can't read individual files |
| 7 | Capability | Can put object | Can read but can't write |
| 8 | Capability | Can delete object | Can write but can't delete |

## Test Structure

Tests are organized by resource with numeric prefixes for execution order:

```
test/api/backend/pre_deployment/integration/
├── conftest.py                        # Shared fixtures
├── test_01_iam_role.py                # IAM/credentials battery (MUST run first)
├── test_02_s3_state_bucket.py         # S3 state bucket battery
└── test_03_central_logs_bucket.py     # Central logs bucket battery
```

The IAM role tests **must run first** because all other tests depend on having valid credentials. If credentials are invalid, all subsequent tests fail with confusing errors.

Within each file, test classes group related checks:

```python
class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""

    def test_02_can_call_sts_api(self, sts_client):
        """Verify credentials are valid."""

class TestS3BucketExistence:
    """Layers 2-3: Verify we can check and the bucket exists."""

    def test_01_can_call_head_bucket_api(self, s3_client, bucket_name):
        """Layer 2: Verify we have permission to check bucket existence."""

    def test_02_bucket_exists(self, s3_client, bucket_name):
        """Layer 3: Verify the bucket exists."""

class TestS3BucketCapability:
    """Layer 5: Verify we can perform required operations."""

    def test_01_can_list_objects(self, s3_client, bucket_name):
        """Verify we can list bucket contents."""

    def test_02_can_put_object(self, s3_client, bucket_name):
        """Verify we can write to the bucket."""
```

## Writing New Test Batteries

When adding pre-deployment tests for a new resource:

1. **Start with authentication**: If it's the first test file, verify credentials work.

2. **Test authorization before existence**: Verify you can call the API before checking if the resource exists.

3. **Test existence before capability**: Verify the resource exists before testing operations on it.

4. **Make each test atomic**: One assertion per test. Don't test multiple things.

5. **Provide actionable failure messages**: Include resource names, expected values, and remediation steps.

6. **Clean up after capability tests**: If testing write operations, delete test artifacts in `finally` blocks.

Example pattern:

```python
def test_01_can_call_api(self, client, resource_id):
    """Layer 2: Verify we have permission to call the API."""
    try:
        client.describe_resource(Id=resource_id)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(f"No permission to call DescribeResource on '{resource_id}'")
        raise

def test_02_resource_exists(self, client, resource_id):
    """Layer 3: Verify the resource exists."""
    try:
        response = client.describe_resource(Id=resource_id)
        assert response["Resource"]["Id"] == resource_id
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFound":
            pytest.fail(f"Resource '{resource_id}' does not exist")
        raise

def test_03_can_write_to_resource(self, client, resource_id):
    """Layer 5: Verify we can perform write operations."""
    try:
        client.update_resource(Id=resource_id, Data="test")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                f"No permission to update '{resource_id}'. "
                "IAM policy may be correct but SCP or resource policy blocking."
            )
        raise
    finally:
        # Clean up test data
        try:
            client.update_resource(Id=resource_id, Data="")
        except ClientError:
            pass
```

## What Not to Test

Pre-deployment tests validate **dependencies**, not the infrastructure being deployed:

- **Do test**: Bootstrap resources that must exist before deployment
- **Do test**: IAM permissions required for deployment
- **Do test**: External resources referenced by terraform

- **Don't test**: Resources created by the deployment itself
- **Don't test**: Application logic or business rules
- **Don't test**: Things covered by unit tests
