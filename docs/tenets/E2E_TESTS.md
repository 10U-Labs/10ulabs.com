# E2E Test Tenets

These are the non-negotiable rules for end-to-end tests.

## 1. Top of the Pyramid

**E2E tests are few in number. Only test critical user journeys.**

```
        /\
       /  \     E2E tests (few) ← YOU ARE HERE
      /----\
     /      \   Integration tests (some)
    /--------\
   /          \
  /            \ Unit tests (many)
 /______________\
```

E2E tests are expensive:
- Slow (seconds to minutes, not milliseconds)
- Flaky (network, timing, external dependencies)
- Run in production (real resources, real costs)

For any system, aim for 3-5 e2e tests max. Each test should represent a critical user journey that, if broken, would constitute a major incident.

```python
# CORRECT - critical user journeys only
def test_webhook_creates_runner():
    """Verify a GitHub webhook results in a running ECS task."""
    ...

def test_invalid_signature_rejected():
    """Verify tampered webhooks are rejected."""
    ...
```

```python
# WRONG - testing edge cases in e2e
def test_webhook_with_empty_labels():
    """Verify webhook with empty labels fails gracefully."""
    # This is a unit test, not e2e
    ...

def test_webhook_with_invalid_json():
    """Verify malformed JSON is rejected."""
    # This is a unit test, not e2e
    ...
```

## 2. Production-Safe

**E2E tests run in production. They must be non-destructive or use test flags.**

There is no staging environment. E2E tests execute against production resources. Every e2e test must follow one of these patterns:

### Pattern A: Read-Only Verification

Test only inspects state, creates nothing.

```python
# CORRECT - read-only
def test_api_gateway_responds(api_endpoint):
    """Verify API Gateway returns 200 for health check."""
    response = requests.get(f"{api_endpoint}/health")
    assert response.status_code == 200
```

### Pattern B: Test Flag with Minimal Side Effects

Test uses a flag that causes the system to skip or minimize resource creation.

```python
# CORRECT - test flag skips resource creation
def test_webhook_processing_with_dry_run(api_endpoint, signed_payload):
    """Verify webhook is processed (dry-run mode)."""
    response = requests.post(
        f"{api_endpoint}/v1/runners",
        headers={
            "X-Hub-Signature-256": signed_payload["signature"],
            "X-Dry-Run": "true"  # System processes but doesn't create runner
        },
        json=signed_payload["body"]
    )
    assert response.status_code == 200
    assert response.json()["dry_run"] is True
```

### Pattern C: Self-Cleanup Resources

Test creates minimal resources that immediately self-terminate.

```python
# CORRECT - self-cleanup
def test_runner_provisioning(api_endpoint, canary_payload):
    """Verify runner is provisioned for canary workflow."""
    # Canary payload uses labels that create a minimal runner
    # Runner runs a 5-second health check and terminates
    response = requests.post(
        f"{api_endpoint}/v1/runners",
        headers=canary_payload["headers"],
        json=canary_payload["body"]
    )
    assert response.status_code == 200

    # Wait for runner to terminate (max 60 seconds)
    task_id = response.json()["task_id"]
    wait_for_task_stopped(task_id, timeout=60)
```

```python
# WRONG - creates persistent resources
def test_runner_provisioning():
    """Verify runner is provisioned."""
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 200
    # No cleanup! Runner keeps running, costing money
```

## 3. Test the Full Path

**E2E tests verify end-to-end behavior that unit and integration tests cannot catch.**

E2E tests exercise the complete path:
- HTTP request → API Gateway → Lambda → SQS → Lambda → Resource

```python
# CORRECT - full path
def test_webhook_to_runner_flow(api_endpoint, signed_webhook):
    """Verify webhook flows through to runner creation."""
    # 1. Send HTTP request
    response = requests.post(
        f"{api_endpoint}/v1/runners",
        headers=signed_webhook["headers"],
        json=signed_webhook["body"]
    )
    assert response.status_code == 200

    # 2. Verify message reached SQS (via CloudWatch logs or metrics)
    assert_log_contains("Enqueued job", timeout=10)

    # 3. Verify runner was created (or would be in dry-run)
    assert_log_contains("Runner started", timeout=30)
```

```python
# WRONG - partial path (this is integration, not e2e)
def test_lambda_processes_sqs_message(lambda_client):
    """Verify Lambda processes SQS message."""
    # Directly invoking Lambda bypasses API Gateway, signature verification, etc.
    response = lambda_client.invoke(
        FunctionName="TenULabsWebhookHandler",
        Payload=json.dumps({"test": "event"})
    )
    assert response["StatusCode"] == 200
```

## 4. Last Line of Defense, Not First

**If an e2e test catches a bug that a unit test should have caught, that's a unit test gap.**

E2E tests should only catch issues that cannot be caught earlier:
- Race conditions in distributed systems
- Network/timing issues between components
- Production configuration drift
- Integration issues between independently-deployed services

| Issue Type | Should Be Caught By |
|------------|---------------------|
| Logic error in label parsing | Unit test |
| Missing null check | Unit test |
| Lambda timeout too short | Post-deployment integration |
| SQS queue missing | Post-deployment integration |
| HTTP request doesn't reach Lambda | E2E test |
| Message lost between SQS and Lambda | E2E test |
| Circuit breaker triggers incorrectly | E2E test |

```python
# CORRECT - catches integration issue
def test_message_flows_through_queue():
    """Verify messages are not lost between SQS and Lambda."""
    # This catches: queue misconfiguration, visibility timeout issues,
    # Lambda trigger not working, dead letter queue problems
    ...
```

```python
# WRONG - should be unit test
def test_labels_parsed_correctly():
    """Verify runner labels are parsed."""
    # This should be tested in unit tests, not e2e
    response = requests.post(endpoint, json={"labels": ["ecs", "arm64"]})
    assert "ecs" in response.json()["runner_type"]
```

## 5. Run During CI/CD

**E2E tests run as workflow steps, not on schedule.**

E2E tests execute:
- As a step in the deployment workflow
- After post-deployment integration tests pass
- Only for the component being deployed

```yaml
# CORRECT - e2e as workflow step
jobs:
  deploy:
    steps:
      - name: Deploy
        run: terraform apply

      - name: Post-deployment integration tests
        run: pytest test/api/endpoints/runners/post_deployment/integration/

      - name: E2E tests
        run: pytest test/api/endpoints/runners/e2e/
```

```yaml
# WRONG - scheduled e2e tests
on:
  schedule:
    - cron: '0 0 * * *'  # We don't run tests on schedule
```

## 6. Fail Fast

**E2E tests should fail quickly when something is wrong.**

Don't wait for long timeouts. If the system is working, responses are fast.

```python
# CORRECT - aggressive timeouts
def test_webhook_response_time(api_endpoint, signed_payload):
    """Verify webhook returns within 5 seconds."""
    start = time.time()
    response = requests.post(
        f"{api_endpoint}/v1/runners",
        headers=signed_payload["headers"],
        json=signed_payload["body"],
        timeout=5  # Fail fast
    )
    elapsed = time.time() - start
    assert elapsed < 5
    assert response.status_code == 200
```

```python
# WRONG - waiting too long
def test_webhook_eventually_works(api_endpoint, payload):
    """Verify webhook works."""
    for attempt in range(30):  # 30 retries?!
        try:
            response = requests.post(endpoint, json=payload, timeout=60)
            if response.status_code == 200:
                return
        except:
            pass
        time.sleep(10)  # Waiting 5 minutes total before failing
    pytest.fail("Webhook never worked")
```

## 7. Clear Ownership

**Each e2e test must document the user journey it validates.**

```python
# CORRECT - clear documentation
def test_github_webhook_provisions_ecs_runner():
    """
    User Journey: GitHub workflow triggers self-hosted ECS runner

    When: A GitHub workflow_job webhook with labels [self-hosted, ecs] arrives
    Then: An ECS task is started to handle the job

    Critical Path: API Gateway → WebhookHandler → JobQueue → SQSHandler → ECS
    Failure Impact: All GitHub Actions using ECS runners will fail
    """
    ...
```

```python
# WRONG - no context
def test_webhook():
    """Test webhook."""
    ...
```

## 8. Test File Organization

```
test/api/endpoints/{endpoint}/e2e/
├── conftest.py           # Fixtures for API endpoints, signed payloads
├── test_happy_path.py    # Critical happy path journeys (1-3 tests)
└── test_security.py      # Critical security journeys (1-2 tests)
```

E2E tests are organized by journey type, not by component. The number of files should be small (2-3 max).

## 9. Fixture Requirements

E2E fixtures must:
1. Create properly signed payloads (real GitHub signature format)
2. Use test flags to minimize production impact
3. Provide cleanup utilities for any resources created

```python
# conftest.py
@pytest.fixture
def api_endpoint(config):
    """Production API endpoint."""
    return config["api_gateway_url"]

@pytest.fixture
def signed_webhook(config):
    """Create a properly signed GitHub webhook payload."""
    payload = {
        "action": "queued",
        "workflow_job": {
            "labels": ["self-hosted", "ecs", "e2e-test"]  # e2e-test label
        }
    }
    signature = sign_payload(payload, config["webhook_secret"])
    return {
        "headers": {
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "workflow_job"
        },
        "body": payload
    }
```

## Quick Reference

| If you want to test... | Test Type | Why |
|------------------------|-----------|-----|
| Label parsing logic | Unit | Pure function, no I/O |
| Error message format | Unit | Pure function, no I/O |
| Lambda timeout is 30s | Post-deployment integration | Resource configuration |
| SQS has Lambda trigger | Post-deployment integration | Component wiring |
| HTTP request reaches Lambda | E2E | Full path verification |
| Webhook signature verified | E2E | Security-critical path |
| Runner actually starts | E2E | End-to-end user journey |

## Boundary with Post-Deployment Integration

Post-deployment integration tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

| Post-Deployment Integration | E2E |
|----------------------------|-----|
| Lambda exists | Lambda responds to HTTP |
| SQS queue exists | Messages flow through queue |
| Lambda has SQS trigger | Trigger actually fires |
| IAM policy attached | IAM policy works in practice |
| Configuration is correct | System behaves correctly |
