# Post-Deployment Integration Test Tenets

These are the non-negotiable rules for post-deployment integration tests.

## 1. Only Test This Deployment's Resources

**Post-deployment tests ONLY test resources created by THIS workflow.**

- Do test: Resources created by terraform apply
- Do test: Resource configuration matches expected values
- Do test: Component wiring (triggers, layers, IAM cross-service)
- Do NOT test: Full user journeys (those are e2e tests)
- Do NOT test: Resources created by other workflows
- Do NOT test: Application logic or business rules (unit tests)

Post-deployment tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

## 2. Three-Layer Testing Model

Every deployed resource must be tested through three layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Existence | Resource was created | Lambda function exists |
| 2. Configuration | Resource configured correctly | SQS queue has 14-day retention |
| 3. Wiring | Components connected properly | Lambda has Layer attached, SQS triggers Lambda |

Each layer catches different failure modes:
- Layer 1 fails → terraform didn't create the resource
- Layer 2 fails → resource exists but misconfigured
- Layer 3 fails → resources exist and configured, but not connected

## 3. Fail Fast with Granular Diagnostics

Cryptic errors like "Lambda invocation failed" are unacceptable.

- Each test must be atomic: one assertion per test
- Tests must run in layer order (existence before configuration before wiring)
- When a test fails, the developer must know exactly what's wrong
- Failure messages must include resource names and expected values

## 4. Test File Organization

Tests must be organized by layer, not by resource:

```
test/api/endpoints/runners/post_deployment/integration/
├── test_01_existence.py       # All resources exist
├── test_02_configuration.py   # All resources configured correctly
└── test_03_wiring.py          # All components connected properly
```

Do NOT organize by resource (test_lambda.py, test_sqs.py, test_dynamodb.py).
This makes it impossible to know which layer failed.

## 5. Boundary with E2E Tests

Post-deployment integration tests verify the deployment. E2E tests verify user journeys.

| Post-Deployment Integration | E2E |
|-----------------------------|-----|
| Lambda exists | Webhook triggers runner |
| SQS queue has correct retention | Message flows through queue |
| Lambda has Layer attached | Full label routing works |
| DynamoDB table has correct keys | Circuit breaker opens on failures |

If a test sends a real webhook, processes a real message flow, or simulates a user action, it belongs in e2e tests.

## 6. No Cleanup Required

Unlike pre-deployment capability tests, post-deployment tests should NOT create test artifacts. They only inspect what terraform created.

- Do: Read resource configuration
- Do: Verify resource exists
- Do: Check component connections
- Do NOT: Write test data to DynamoDB
- Do NOT: Send test messages to SQS
- Do NOT: Invoke Lambdas with test payloads (that's e2e)

## Quick Reference

| Layer | Tests | Failure Means |
|-------|-------|---------------|
| 1. Existence | Resource exists in AWS | Terraform didn't create it |
| 2. Configuration | Settings match expected | Created but misconfigured |
| 3. Wiring | Components connected | Exists, configured, but not wired |
