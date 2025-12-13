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

## 2. Five-Layer Testing Model

Every resource dependency must be tested through five layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Authentication | Valid credentials exist | Can call sts:GetCallerIdentity |
| 2. Authorization | Permission to inspect resources | Can call s3:HeadBucket |
| 3. Existence | Resource actually exists | Bucket exists |
| 4. Configuration | Resource configured correctly | IAM role has required policy |
| 5. Capability | Can perform required operations | Can call s3:PutObject |

Each layer catches different failure modes. When Layer 3 fails but Layers 1-2 pass, you know credentials are valid and you have permission to check, but the resource doesn't exist.

## 3. Fail Fast with Granular Diagnostics

Cryptic errors like "AccessDenied: Access Denied" are unacceptable.

- Each test must be atomic: one assertion per test
- Tests must run in dependency order
- When a test fails, the developer must know exactly where the chain broke
- Failure messages must include resource names, expected values, and remediation steps

## 4. Test Ordering

Tests must be organized with numeric prefixes for execution order:

```
test/api/backend/pre_deployment/integration/
├── test_01_iam_role.py                # MUST run first - all other tests depend on credentials
├── test_02_s3_state_bucket.py
└── test_03_central_logs_bucket.py
```

IAM/authentication tests always run first. If credentials are invalid, all subsequent tests fail with confusing errors.

## 5. Cleanup After Capability Tests

If testing write operations, delete test artifacts in `finally` blocks.

```python
def test_can_write(self, client, resource_id):
    try:
        client.put_item(Id=resource_id, Data="test")
    finally:
        try:
            client.delete_item(Id=resource_id)
        except ClientError:
            pass
```

No test artifacts should remain after test execution.

## Quick Reference

| Workflow | Pre-deployment tests should check | NOT check |
|----------|-----------------------------------|-----------|
| `endpoint_v1_runners` | IAM role from bootstrap, API Gateway from api_backend | SQS queues, DynamoDB tables (created by this workflow) |
| `api_backend` | S3 buckets from bootstrap | API Gateway, Lambda functions (created by this workflow) |
| `endpoint_v1_health` | API Gateway from api_backend | Lambda function (created by this workflow) |
