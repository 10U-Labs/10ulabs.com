# Runners Endpoint: Test Coverage & Robustness Analysis

## Executive Summary

The current implementation has good basic test coverage (~98% for webhook_router.py) but lacks:
1. **Tests for configure_webhook_handler.py** (0% coverage for Custom Resource Lambda)
2. **Edge case handling** for production robustness
3. **HA/self-healing capabilities** for mission-critical webhook processing

## 1. Test Coverage Analysis

### ✅ Well-Covered Components

**webhook_router.py** (41 unit tests, ~98% coverage):
- Lambda handler: base64 encoding, form encoding, invalid JSON, signature validation
- Event routing: ping, workflow_job, unknown events
- Signature verification: valid/invalid/missing signatures
- Workflow job handling: queued/completed actions, label filtering
- Runner routing: EC2/Fargate/unknown types
- Secret management: client caching, secret caching
- Error handling: network failures, JSON parsing errors

**Integration tests** (19 tests):
- Stack deployment verification
- Lambda function configuration (runtime, timeout, memory, env vars)
- IAM permissions (Secrets Manager access)
- API Gateway configuration (resource, method, Lambda integration)
- CloudWatch logs
- Stack outputs

**E2E tests** (10 tests):
- Live endpoint ping/pong
- Workflow job event handling (queued/completed/filtered)
- Invalid JSON handling
- Unknown event types

### ❌ Missing Test Coverage

#### A. configure_webhook_handler.py (0% coverage)
**Critical Gap**: No tests for Custom Resource Lambda that configures GitHub webhooks

**Missing unit tests**:
- `get_github_pat()`: Success, failure, missing secret
- `get_or_create_webhook_secret()`: Get existing, create new, conflict handling
- `create_github_webhook()`: Success, HTTP errors (422 duplicate, 401 auth, 403 permissions), network errors, timeout
- `delete_github_webhook()`: Success, 404 not found, HTTP errors
- `send_response()`: Success, network failure, invalid response URL
- `lambda_handler()`: Create event, Update event, Delete event, missing properties, invalid request types

**Missing integration tests**:
- Verify webhook created in GitHub
- Verify webhook secret stored in Secrets Manager
- Verify webhook deleted on stack destroy
- Verify Custom Resource rollback on failure

#### B. CloudFormation Export Dependencies
**Missing tests**:
- Verify `Fn.import_value("GitHubAuth-PATSecretName")` works correctly
- Verify stack deployment fails gracefully if auth stack not deployed
- Verify error messages when exports not found

#### C. Config Validation
**Missing tests**:
- `test_config_has_github_repository`: Verify repository field exists
- Test removed `secrets_manager` section doesn't break anything

#### D. Lambda Configuration
**Missing integration tests**:
- Verify webhook_config_lambda exists and has correct configuration
- Verify Custom Resource provider exists
- Verify IAM permissions for webhook_config_lambda (CreateSecret)

## 2. Edge & Interruption Cases

### ⚠️ Current Gaps

#### A. webhook_router.py Edge Cases

**1. Secrets Manager Failures**
```python
# Current: Returns empty string, continues without signature verification
def get_webhook_secret() -> str:
    ...
    except ClientError as e:
        logger.error("Failed to retrieve webhook secret: %s", e)
        return ''  # ❌ Proceeds without security!
```
**Issue**: If Secrets Manager is down, webhooks are accepted WITHOUT signature verification
**Risk**: Security vulnerability - unauthenticated requests accepted

**2. Downstream Endpoint Failures (No Retry)**
```python
# Current: Single attempt, no retry
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        ...
except (urllib.error.URLError, ValueError) as e:
    logger.error("Failed to route job %s to %s runner: %s", job_id, runner_type, e)
    return {'success': False, 'error': str(e)}  # ❌ Job lost
```
**Issue**: Transient network failures cause job loss
**Risk**: GitHub workflow jobs fail permanently

**3. Timeout Handling**
```python
# Current: 30s timeout, no handling for partial responses
with urllib.request.urlopen(req, timeout=30) as response:
```
**Issue**: Hard timeout, no graceful degradation
**Risk**: Jobs timeout but may have been partially processed (duplicate runners)

**4. Signature Verification Edge Cases**
```python
# Current: Splits without validation
_, github_signature = signature_header.split('=')  # ❌ Can raise ValueError
```
**Issue**: Malformed signature header causes 500 error instead of 401
**Risk**: Poor error responses

**5. Concurrency (Lambda Cold Starts)**
**Issue**: Module-level caching doesn't persist across cold starts
**Risk**: Every cold start hits Secrets Manager (rate limits, costs)

**6. Request Size Limits**
**Issue**: No validation of payload size (API Gateway max: 10MB)
**Risk**: Large payloads cause OOM errors

#### B. configure_webhook_handler.py Edge Cases

**1. Webhook Duplication**
```python
# Current: No check for existing webhooks
def create_github_webhook(...):
    # ❌ Always creates new webhook, GitHub allows duplicates
```
**Issue**: Multiple stack deployments create duplicate webhooks
**Risk**: GitHub sends webhooks multiple times, duplicate runners launched

**2. Secret Rotation**
```python
# Current: Creates secret once, never updates
def get_or_create_webhook_secret():
    except client.exceptions.ResourceNotFoundException:
        client.create_secret(Name=secret_name, ...)  # ❌ No rotation
```
**Issue**: Secret never rotated, no expiration
**Risk**: Long-lived secrets increase compromise risk

**3. CloudFormation Rollback**
```python
# Current: Webhook created, then stack fails → webhook orphaned
def lambda_handler(event, _context):
    result = create_github_webhook(...)
    if result['success']:
        send_response(event, 'SUCCESS', ...)  # ❌ No cleanup on later failure
```
**Issue**: Webhook left in GitHub if stack creation fails after webhook created
**Risk**: Orphaned webhooks point to non-existent endpoints

**4. Update Operation**
```python
# Current: Creates new webhook on Update
if request_type in ['Create', 'Update']:
    result = create_github_webhook(...)  # ❌ Should update existing, not create new
```
**Issue**: Stack updates create duplicate webhooks
**Risk**: Multiple active webhooks

**5. GitHub API Rate Limiting**
```python
# Current: No retry logic for 429 rate limit errors
except urllib.error.HTTPError as e:
    logger.error("Failed to create webhook: %s - %s", e.code, error_body)
    return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}  # ❌ No retry
```
**Issue**: Rate limited requests fail stack deployment
**Risk**: Stack creation fails, requires manual intervention

**6. Concurrent Stack Operations**
**Issue**: No locking mechanism for secret creation
**Risk**: Race condition if multiple stacks create webhook secret simultaneously

### ⚠️ Interruption Scenarios

**1. Lambda Timeout (60s)**
```
Scenario: GitHub API slow → Lambda times out → CloudFormation CREATE_FAILED
Impact: Stack creation fails, webhook may or may not be created (unknown state)
```

**2. Lambda OOM**
```
Scenario: 256MB memory exhausted → Lambda killed → CloudFormation CREATE_FAILED
Impact: Same as timeout
```

**3. Secrets Manager Outage**
```
Scenario: Secrets Manager unavailable → Lambda can't get PAT → CREATE_FAILED
Impact: Stack deployment blocked until Secrets Manager recovers
```

**4. GitHub API Outage**
```
Scenario: GitHub API down → webhook creation fails → CREATE_FAILED
Impact: Stack deployment blocked until GitHub recovers
```

**5. Network Partition**
```
Scenario: VPC networking issue → Lambda can't reach GitHub → timeout
Impact: Stack deployment fails
```

**6. GitHub Webhook Delivery Failure**
```
Scenario: GitHub sends webhook → API Gateway down → GitHub retries → eventual failure
Impact: Workflow jobs queue but never execute (lost jobs)
```

## 3. Architectural Improvements for HA/Robustness

### 🏗️ Recommended Changes

#### A. Add Dead Letter Queue (DLQ)

**Current Architecture**:
```
GitHub Webhook → API Gateway → Lambda → Runner Endpoint
                                   ↓ (failure)
                                   ❌ Job Lost
```

**Improved Architecture**:
```
GitHub Webhook → API Gateway → Lambda → Runner Endpoint
                                   ↓ (failure)
                               SQS DLQ → Lambda (retry processor)
                                          ↓ (persistent failure)
                                      SNS → Alert/Manual Review
```

**Benefits**:
- Failed jobs preserved for retry
- Automatic retry with exponential backoff
- Alerts for persistent failures
- No job loss during transient failures

**Implementation**:
```python
# stack.py
dlq = sqs.Queue(
    self, "WebhookDLQ",
    retention_period=Duration.days(14),  # Keep failed jobs for 2 weeks
    encryption=sqs.QueueEncryption.KMS_MANAGED
)

webhook_router_lambda.add_event_source(
    lambda_event_sources.SqsEventSource(dlq,
        batch_size=1,
        max_concurrency=5
    )
)

webhook_router_lambda.add_to_role_policy(
    iam.PolicyStatement(
        actions=["sqs:SendMessage"],
        resources=[dlq.queue_arn]
    )
)
```

#### B. Add Retry Logic with Exponential Backoff

**webhook_router.py**:
```python
import time
from typing import Dict, Any, Optional

def route_runner_request_with_retry(
    job_id: int,
    job_labels: List[str],
    github_repo: str,
    max_retries: int = 3
) -> Dict[str, Any]:

    for attempt in range(max_retries):
        result = route_runner_request(job_id, job_labels, github_repo)

        if result['success']:
            return result

        if attempt < max_retries - 1:
            wait_time = (2 ** attempt)  # Exponential: 1s, 2s, 4s
            logger.warning(
                "Retry %d/%d for job %s after %ds",
                attempt + 1, max_retries, job_id, wait_time
            )
            time.sleep(wait_time)

    return result  # Final failure
```

**Benefits**:
- Resilient to transient network failures
- Reduces job loss from temporary outages
- Configurable retry strategy

#### C. Add Idempotency Handling

**Problem**: Duplicate webhook deliveries (GitHub retry mechanism) → duplicate runners

**Solution**: Add idempotency key tracking

**Implementation**:
```python
# Add DynamoDB table for idempotency
idempotency_table = dynamodb.Table(
    self, "WebhookIdempotency",
    partition_key=dynamodb.Attribute(
        name="job_id",
        type=dynamodb.AttributeType.STRING
    ),
    time_to_live_attribute="ttl",
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    removal_policy=RemovalPolicy.DESTROY
)

# Lambda code
def is_duplicate_request(job_id: str) -> bool:
    try:
        table.put_item(
            Item={'job_id': str(job_id), 'ttl': int(time.time()) + 3600},
            ConditionExpression='attribute_not_exists(job_id)'
        )
        return False  # New request
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return True  # Duplicate
        raise
```

**Benefits**:
- Prevents duplicate runner launches
- Handles GitHub's retry mechanism safely
- TTL auto-cleanup (1 hour expiration)

#### D. Add Circuit Breaker Pattern

**Problem**: Downstream endpoint down → all webhooks fail → Lambda waste

**Solution**: Circuit breaker stops calling failing endpoints

**Implementation**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = 'OPEN'
            raise

# Usage
ec2_circuit_breaker = CircuitBreaker()
fargate_circuit_breaker = CircuitBreaker()
```

**Benefits**:
- Fast failure when endpoint is down
- Reduces unnecessary retries
- Auto-recovery after timeout

#### E. Add Reserved Concurrency Limits

**Problem**: Webhook flood → all Lambda capacity consumed → other services starved

**Solution**: Set reserved concurrency for webhook Lambda

**Implementation**:
```python
webhook_router_lambda = lambda_.Function(
    ...
    reserved_concurrent_executions=100,  # Max 100 concurrent executions
)
```

**Benefits**:
- Prevents webhook flood from consuming all Lambda capacity
- Protects other services in the account
- Predictable behavior under load

#### F. Add Async Processing with SQS

**Current**: Synchronous processing (webhook waits for runner launch)
**Problem**: Slow runner launches timeout API Gateway (29s limit)

**Improved Architecture**:
```
GitHub Webhook → API Gateway → Lambda (enqueue) → SQS → Lambda (processor)
      ↓ (200 OK immediately)                              ↓
                                                    Runner Endpoint
```

**Benefits**:
- Fast webhook ACK (sub-second)
- No API Gateway timeout issues
- Batch processing capability
- Rate limiting via SQS throttling

**Implementation**:
```python
# stack.py
webhook_queue = sqs.Queue(
    self, "WebhookQueue",
    visibility_timeout=Duration.seconds(120),
    retention_period=Duration.days(4),
    encryption=sqs.QueueEncryption.KMS_MANAGED
)

processor_lambda = lambda_.Function(
    self, "WebhookProcessor",
    ...
    timeout=Duration.seconds(120),
    reserved_concurrent_executions=50
)

processor_lambda.add_event_source(
    lambda_event_sources.SqsEventSource(
        webhook_queue,
        batch_size=1,
        max_concurrency=10,
        report_batch_item_failures=True  # Partial batch failure support
    )
)

# webhook_router.py (simplified)
def lambda_handler(event, _context):
    # Verify signature
    # Validate payload
    # Enqueue to SQS
    sqs.send_message(
        QueueUrl=os.environ['QUEUE_URL'],
        MessageBody=json.dumps(payload)
    )
    return {'statusCode': 200, 'body': json.dumps({'message': 'Accepted'})}
```

#### G. Add Monitoring & Alarms

**Current**: Logging only, no proactive alerting

**Improvements**:
```python
# CloudWatch Alarms
lambda_errors = cloudwatch.Alarm(
    self, "WebhookRouterErrors",
    metric=webhook_router_lambda.metric_errors(),
    threshold=5,
    evaluation_periods=1,
    alarm_description="Lambda errors > 5 in 1 minute"
)

lambda_throttles = cloudwatch.Alarm(
    self, "WebhookRouterThrottles",
    metric=webhook_router_lambda.metric_throttles(),
    threshold=1,
    evaluation_periods=1,
    alarm_description="Lambda throttled"
)

dlq_messages = cloudwatch.Alarm(
    self, "DLQMessages",
    metric=dlq.metric_approximate_number_of_messages_visible(),
    threshold=10,
    evaluation_periods=1,
    alarm_description="DLQ has > 10 messages"
)

# Custom Metrics
from aws_cdk import aws_cloudwatch as cloudwatch

cloudwatch.Metric(
    namespace="GitHubWebhooks",
    metric_name="JobRoutingSuccess",
    statistic="Sum"
)
```

**Lambda code**:
```python
from aws_embedded_metrics import metric_scope

@metric_scope
def lambda_handler(event, _context, metrics):
    metrics.put_metric("WebhookReceived", 1, "Count")

    result = route_runner_request(...)

    if result['success']:
        metrics.put_metric("JobRoutingSuccess", 1, "Count")
    else:
        metrics.put_metric("JobRoutingFailure", 1, "Count")
```

#### H. Add Secret Rotation for Webhook Secret

**Current**: Static secret, never rotated

**Improvement**:
```python
# stack.py
webhook_secret = secretsmanager.Secret(
    self, "WebhookSecret",
    secret_name="api-webhook-secret",
    generate_secret_string=secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"version": "v1"}),
        generate_string_key="secret",
        exclude_characters='\\"\'"@',
        password_length=32
    ),
    rotation_schedule=secretsmanager.RotationSchedule(
        automatically_after=Duration.days(90)
    )
)

# Rotation Lambda updates GitHub webhook with new secret
rotation_lambda = lambda_.Function(...)
webhook_secret.add_rotation_schedule("WebhookSecretRotation",
    rotation_lambda=rotation_lambda,
    automatically_after=Duration.days(90)
)
```

#### I. Improve configure_webhook_handler.py Robustness

**1. Check for Existing Webhooks**:
```python
def get_existing_webhook(repo: str, github_pat: str, webhook_url: str) -> Optional[int]:
    api_endpoint = f'https://api.github.com/repos/{repo}/hooks'
    req = urllib.request.Request(api_endpoint,
        headers={'Authorization': f'token {github_pat}'})

    with urllib.request.urlopen(req, timeout=30) as response:
        hooks = json.loads(response.read())
        for hook in hooks:
            if hook.get('config', {}).get('url') == webhook_url:
                return hook['id']
    return None

def create_or_update_github_webhook(...):
    existing_id = get_existing_webhook(repo, github_pat, webhook_url)
    if existing_id:
        return update_github_webhook(existing_id, ...)  # Update instead of create
    else:
        return create_github_webhook(...)
```

**2. Add Retry Logic**:
```python
def create_github_webhook_with_retry(..., max_retries=3):
    for attempt in range(max_retries):
        try:
            return create_github_webhook(...)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limit
                wait_time = int(e.headers.get('Retry-After', 60))
                logger.warning("Rate limited, waiting %ds", wait_time)
                time.sleep(wait_time)
                continue
            elif e.code >= 500:  # Server error
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            raise
```

**3. Add Cleanup on Failure**:
```python
def lambda_handler(event, _context):
    webhook_id = None
    try:
        result = create_github_webhook(...)
        if result['success']:
            webhook_id = result['webhook_id']
            # ... rest of processing
    except Exception as e:
        if webhook_id:
            logger.warning("Cleaning up webhook %s due to error", webhook_id)
            delete_github_webhook(webhook_id, github_pat, repo)
        send_response(event, 'FAILED', str(e), physical_resource_id, {})
        raise
```

#### J. Add Health Check Endpoint

**Purpose**: Allow GitHub to verify endpoint is alive before sending webhooks

**Implementation**:
```python
# Add /v1/runners/health endpoint
health_resource = runners_resource.add_resource("health")
health_resource.add_method("GET",
    apigw.MockIntegration(
        integration_responses=[{
            'statusCode': '200',
            'responseTemplates': {
                'application/json': '{"status": "healthy"}'
            }
        }],
        request_templates={
            'application/json': '{"statusCode": 200}'
        }
    ),
    method_responses=[{
        'statusCode': '200'
    }]
)
```

## 4. Priority Recommendations

### 🔴 Critical (Implement Immediately)

1. **Add tests for configure_webhook_handler.py** (security risk - untested webhook config)
2. **Fix signature verification to fail closed** (security risk - accepts requests without auth)
3. **Add duplicate webhook detection** (duplicate runners = wasted compute)
4. **Add retry logic with exponential backoff** (job loss during transient failures)

### 🟡 High Priority (Implement Soon)

5. **Add DLQ for failed webhooks** (job loss prevention)
6. **Add idempotency handling** (prevent duplicate runners)
7. **Add CloudWatch alarms** (operational visibility)
8. **Add reserved concurrency limits** (prevent resource exhaustion)

### 🟢 Medium Priority (Nice to Have)

9. **Migrate to async processing with SQS** (better scalability)
10. **Add circuit breaker pattern** (faster failure)
11. **Add webhook secret rotation** (security best practice)
12. **Add health check endpoint** (monitoring)

## 5. Suggested Test Additions

### A. Unit Tests for configure_webhook_handler.py

Create `test/api/runners/test_webhook_config_unit.py`:
```python
def test_get_github_pat_success()
def test_get_github_pat_handles_missing_secret()
def test_get_github_pat_handles_access_denied()

def test_get_or_create_webhook_secret_returns_existing()
def test_get_or_create_webhook_secret_creates_new()
def test_get_or_create_webhook_secret_handles_race_condition()

def test_create_github_webhook_success()
def test_create_github_webhook_handles_422_duplicate()
def test_create_github_webhook_handles_401_unauthorized()
def test_create_github_webhook_handles_403_forbidden()
def test_create_github_webhook_handles_404_not_found()
def test_create_github_webhook_handles_rate_limit()
def test_create_github_webhook_handles_timeout()
def test_create_github_webhook_handles_network_error()

def test_delete_github_webhook_success()
def test_delete_github_webhook_handles_404()
def test_delete_github_webhook_handles_http_error()

def test_lambda_handler_create_event()
def test_lambda_handler_update_event()
def test_lambda_handler_delete_event()
def test_lambda_handler_invalid_request_type()
def test_lambda_handler_sends_cfn_response()
```

### B. Edge Case Tests for webhook_router.py

Add to `test/api/runners/test_unit.py`:
```python
def test_verify_signature_handles_malformed_header()
def test_verify_signature_handles_missing_algorithm()
def test_verify_signature_handles_empty_secret()

def test_get_webhook_secret_handles_throttling()
def test_get_webhook_secret_refreshes_after_expiration()

def test_route_runner_request_handles_partial_response()
def test_route_runner_request_handles_connection_reset()
def test_route_runner_request_handles_ssl_error()

def test_handle_workflow_job_handles_missing_fields()
def test_handle_workflow_job_handles_malformed_data()

def test_lambda_handler_handles_oversized_payload()
def test_lambda_handler_handles_missing_headers()
```

### C. Integration Tests

Add to `test/api/runners/test_integration.py`:
```python
def test_webhook_config_lambda_exists()
def test_webhook_config_lambda_has_correct_permissions()
def test_custom_resource_provider_exists()
def test_github_webhook_configured_in_repo()
def test_webhook_secret_exists_in_secrets_manager()
```

### D. E2E Tests for Robustness

Add to `test/api/runners/test_e2e.py`:
```python
def test_endpoint_handles_concurrent_requests()
def test_endpoint_handles_large_payloads()
def test_endpoint_handles_slow_responses()
def test_endpoint_returns_429_on_rate_limit()
```

## 6. Summary

**Current State**:
- Good basic test coverage for webhook_router.py
- Zero test coverage for configure_webhook_handler.py
- Missing edge case handling
- No HA/self-healing capabilities

**Recommended Path**:
1. Add unit tests for configure_webhook_handler.py (critical security gap)
2. Fix signature verification to fail closed (security fix)
3. Add DLQ + retry logic (prevent job loss)
4. Add idempotency (prevent duplicate runners)
5. Add monitoring/alarms (operational visibility)
6. Consider async processing with SQS (scalability)

**Estimated Effort**:
- Test additions: 2-3 days
- Critical fixes: 1-2 days
- HA improvements: 3-5 days
- Total: 1-2 weeks for production-ready implementation
