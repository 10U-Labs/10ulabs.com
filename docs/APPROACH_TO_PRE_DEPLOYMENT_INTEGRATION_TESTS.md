# Approach to Pre-Deployment Integration Tests

Pre-deployment integration tests validate that infrastructure dependencies exist and are properly configured **before** attempting deployment. This catches misconfigurations early with precise diagnostic information.

## Philosophy: Fail Fast with Granular Diagnostics

When a deployment fails, the error message is often cryptic:

```
Error: AccessDenied: Access Denied
```

This tells you nothing about *why* access was denied. Was the resource missing? Did the role exist but lack permissions? Did the policy exist but an SCP block the action?

Our approach uses a **battery of atomic tests** ordered by dependency. When a test fails, you know exactly where the chain broke.

## Three-Layer Testing Model

Each resource is tested through three layers:

### Layer 1: Existence
Does the resource exist at all?

```
Test: Does the IAM role exist?
Pass: Role exists, continue testing
Fail: "GitHub Actions role 'X' does not exist"
```

### Layer 2: Configuration
Is the resource configured correctly?

```
Test: Does the role have AdministratorAccess policy attached?
Pass: Policy attached, continue testing
Fail: "Role missing AdministratorAccess policy. Attached policies: [...]"
```

### Layer 3: Capability
Can we actually exercise the permission?

```
Test: Can we call s3:PutObject?
Pass: Write succeeded
Fail: "No permission to call s3:PutObject on 'bucket-name'"
```

## Diagnostic Chain Example

Consider S3 state bucket access. The test battery runs in order:

| Order | Test | Failure Meaning |
|-------|------|-----------------|
| 1 | Can call HeadBucket API | No permission to even check if bucket exists |
| 2 | Bucket exists | Bucket was deleted or never created |
| 3 | Can list objects | Bucket exists but can't read contents |
| 4 | Can get object | Can list but can't read individual files |
| 5 | Can put object | Can read but can't write |
| 6 | Can delete object | Can write but can't delete |

If test 3 fails but tests 1-2 pass, you know:
- You have permission to check bucket existence
- The bucket exists
- Something blocks ListObjectsV2 (SCP? bucket policy? missing IAM permission?)

This precision eliminates guesswork.

## Layer 2 vs Layer 3: Why Both?

Layer 2 checks policy *configuration*. Layer 3 checks actual *capability*.

They can diverge:
- Policy grants permission, but an SCP blocks it → Layer 2 passes, Layer 3 fails
- Policy grants permission, but resource policy denies it → Layer 2 passes, Layer 3 fails
- Policy appears correct, but wrong resource ARN → Layer 2 passes, Layer 3 fails

When Layer 2 passes but Layer 3 fails, you know the IAM policy is correct but something external blocks the action.

## Test Structure

Tests are organized by resource with numeric prefixes for ordering:

```
test/www/shared/pre_deployment/integration/
├── conftest.py                    # Shared fixtures
├── test_01_iam_role.py            # IAM role battery
├── test_02_s3_state_bucket.py     # S3 state bucket battery
└── test_03_route53_zone.py        # Route53 zone battery
```

Within each file, test classes group related checks:

```python
class TestZoneExistenceAndReadCapability:
    """Layer 1/3a: Verify zone exists and we can read from it."""

    def test_01_can_call_route53_get_hosted_zone_api(self, ...):
        """Verify we have permission to call route53:GetHostedZone."""

    def test_02_hosted_zone_exists(self, ...):
        """Verify the Route53 hosted zone exists."""

    def test_03_can_list_resource_record_sets(self, ...):
        """Verify we can call route53:ListResourceRecordSets."""
```

## Writing New Test Batteries

When adding pre-deployment tests for a new resource:

1. **Identify the dependency chain**: What must be true before deployment can succeed?

2. **Order tests by dependency**: Test existence before configuration, configuration before capability.

3. **Make each test atomic**: One assertion per test. Don't test multiple things.

4. **Provide actionable failure messages**: Include resource names, expected values, and actual values.

5. **Clean up after capability tests**: If testing write operations, delete test artifacts in `finally` blocks.

Example pattern:

```python
def test_01_can_call_api(self, client, resource_id):
    """Verify we have permission to call the API."""
    try:
        client.describe_resource(Id=resource_id)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(f"No permission to call DescribeResource on '{resource_id}'")
        raise

def test_02_resource_exists(self, client, resource_id):
    """Verify the resource exists."""
    try:
        response = client.describe_resource(Id=resource_id)
        assert response["Resource"]["Id"] == resource_id
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFound":
            pytest.fail(f"Resource '{resource_id}' does not exist")
        raise
```

## What Not to Test

Pre-deployment tests validate **dependencies**, not the infrastructure being deployed:

- **Do test**: Bootstrap resources that must exist before deployment
- **Do test**: IAM permissions required for deployment
- **Do test**: External resources referenced by terraform

- **Don't test**: Resources created by the deployment itself
- **Don't test**: Application logic or business rules
- **Don't test**: Things covered by unit tests
