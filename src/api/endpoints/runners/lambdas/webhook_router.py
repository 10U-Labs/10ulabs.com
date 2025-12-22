"""Webhook router Lambda handler - routes GitHub webhooks to queues."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote

from botocore.exceptions import ClientError

from common.aws_clients import get_dynamodb_client, get_sqs_client, get_ssm_client
from common.cloudwatch import publish_metric as _common_publish_metric
from common.webhook_ingress import IngressHandler
from runner_labels import get_runner_type_from_labels

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METRICS_NAMESPACE = "WebhookRouter"

_cache: dict[str, Any] = {
    "webhook_secret": None,
    "test_mode": False,
}


def _set_test_mode(enabled: bool) -> None:
    """Set test mode."""
    _cache["test_mode"] = enabled


def _publish_metric(metric_name: str, value: float, unit: str = "None") -> None:
    """Publish a metric to CloudWatch (with test mode check)."""
    if _cache["test_mode"]:
        return
    _common_publish_metric(METRICS_NAMESPACE, metric_name, value, unit)


async def _check_and_record_idempotency(request_id: str) -> bool:
    """Check and record idempotency for a request.

    Returns:
        True if duplicate, False if new request
    """
    table_name = os.environ.get("IDEMPOTENCY_TABLE_NAME")
    if not table_name:
        logger.warning("IDEMPOTENCY_TABLE_NAME not set, skipping idempotency check")
        return False

    try:
        ttl = int(time.time()) + 86400
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                "request_id": {"S": request_id},
                "ttl": {"N": str(ttl)},
                "timestamp": {"N": str(int(time.time()))},
            },
            ConditionExpression="attribute_not_exists(request_id)",
        )
        return False
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        if error_code == "ConditionalCheckFailedException":
            logger.warning("Duplicate request detected: %s", request_id)
            return True
        logger.error("Failed to check idempotency: %s", str(err))
        return False


async def _enqueue_job(job_data: dict[str, Any]) -> dict[str, Any]:
    """Enqueue a job to the job queue.

    Returns:
        Result dictionary with success status
    """
    queue_url = os.environ.get("JOB_QUEUE_URL")
    if not queue_url:
        logger.error("JOB_QUEUE_URL not set, cannot enqueue job")
        return {"success": False, "error": "Job queue not configured"}

    try:
        response = get_sqs_client().send_message(
            QueueUrl=queue_url, MessageBody=json.dumps(job_data)
        )
        logger.info("Enqueued job to SQS: %s", response.get("MessageId"))

        attrs = get_sqs_client().get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
        )
        queue_depth = int(
            attrs.get("Attributes", {}).get("ApproximateNumberOfMessages", "0")
        )
        _publish_metric("QueueDepth", float(queue_depth), "Count")

        return {"success": True, "message_id": response.get("MessageId")}
    except ClientError as err:
        logger.error("Failed to enqueue job: %s", str(err))
        return {"success": False, "error": str(err)}


def _enqueue_ignored_event(event_data: dict[str, Any], reason: str) -> dict[str, Any]:
    """Enqueue an ignored event to the ignored events queue.

    Returns:
        Result dictionary with success status
    """
    queue_url = os.environ.get("IGNORED_EVENTS_QUEUE_URL")
    if not queue_url:
        logger.warning(
            "IGNORED_EVENTS_QUEUE_URL not set, skipping ignored event enqueue"
        )
        return {"success": False, "error": "Ignored events queue not configured"}

    try:
        message_body = {
            "event_data": event_data,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        response = get_sqs_client().send_message(
            QueueUrl=queue_url, MessageBody=json.dumps(message_body)
        )
        logger.info(
            "Enqueued ignored event to SQS: %s (reason: %s)",
            response.get("MessageId"),
            reason,
        )
        return {"success": True, "message_id": response.get("MessageId")}
    except ClientError as err:
        logger.error("Failed to enqueue ignored event: %s", str(err))
        return {"success": False, "error": str(err)}


async def _enqueue_cancellation(cancellation_data: dict[str, Any]) -> dict[str, Any]:
    """Enqueue a cancellation to the cancellation queue.

    Returns:
        Result dictionary with success status
    """
    queue_url = os.environ.get("CANCELLATION_QUEUE_URL")
    if not queue_url:
        logger.warning("CANCELLATION_QUEUE_URL not set, skipping cancellation enqueue")
        return {"success": False, "error": "Cancellation queue not configured"}

    try:
        response = get_sqs_client().send_message(
            QueueUrl=queue_url, MessageBody=json.dumps(cancellation_data)
        )
        logger.info(
            "Enqueued cancellation to SQS: %s (job_id: %s, run_id: %s)",
            response.get("MessageId"),
            cancellation_data.get("job_id"),
            cancellation_data.get("run_id"),
        )
        return {"success": True, "message_id": response.get("MessageId")}
    except ClientError as err:
        logger.error("Failed to enqueue cancellation: %s", str(err))
        return {"success": False, "error": str(err)}


def _handle_workflow_run(event_data: dict[str, Any]) -> dict[str, Any]:
    """Handle a workflow_run event."""
    action = event_data.get("action")
    workflow_run = event_data.get("workflow_run", {})
    run_id = workflow_run.get("id")
    workflow_name = workflow_run.get("name")
    conclusion = workflow_run.get("conclusion")

    logger.info(
        "Workflow run %s %s: workflow=%s, conclusion=%s (ephemeral runners self-cleanup)",
        run_id,
        action,
        workflow_name,
        conclusion,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Workflow run {action} acknowledged",
                "run_id": run_id,
                "conclusion": conclusion,
            }
        ),
    }


async def _get_webhook_secret(force_refresh: bool = False) -> str:
    """Get webhook secret from SSM Parameter Store with caching.

    Returns:
        Webhook secret string

    Raises:
        RuntimeError: If secret cannot be retrieved
    """
    if force_refresh:
        _cache["webhook_secret"] = None

    if _cache["webhook_secret"]:
        return _cache["webhook_secret"]

    parameter_name = os.environ.get("WEBHOOK_SECRET_NAME")
    try:
        response = get_ssm_client().get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        secret = response.get("Parameter", {}).get("Value", "")
        _cache["webhook_secret"] = secret
        return secret
    except ClientError as err:
        logger.error("Failed to retrieve webhook secret: %s", str(err))
        raise RuntimeError(f"Cannot retrieve webhook secret: {err}") from err


def _verify_signature(payload_body: str, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature_header:
        return False

    parts = signature_header.split("=")
    if len(parts) != 2:
        return False

    github_signature = parts[1]
    computed_signature = hmac.new(
        secret.encode("utf-8"), payload_body.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, github_signature)


async def _handle_workflow_job(event_data: dict[str, Any]) -> dict[str, Any]:
    """Handle a workflow_job event."""
    action = event_data.get("action")
    job = event_data.get("workflow_job", {})
    job_id = job.get("id")
    job_name = job.get("name")
    job_labels = job.get("labels", [])
    job_status = job.get("status")
    run_id = job.get("run_id")
    repo_full_name = event_data.get("repository", {}).get("full_name")

    logger.info(
        "Received workflow_job event: action=%s, job=%s, status=%s, labels=%s",
        action,
        job_name,
        job_status,
        json.dumps(job_labels),
    )
    logger.info("workflow_job context: repo=%s, run_id=%s", repo_full_name, run_id)

    if action != "queued":
        logger.info("Ignoring action '%s' (only handle 'queued')", action)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Ignored action: {action}"}),
        }

    runner_type, _ = get_runner_type_from_labels(job_labels)
    if not runner_type:
        logger.info(
            "Job labels %s don't contain EC2 or Fargate runner type labels",
            json.dumps(job_labels),
        )
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No matching runner type, ignoring"}),
        }

    logger.info(
        "Enqueueing runner request for job %s (%s), runner_type=%s",
        job_id,
        job_name,
        runner_type,
    )

    job_data = {
        "job_id": job_id,
        "job_labels": job_labels,
        "github_repo": repo_full_name,
        "run_id": run_id,
        "runner_type": runner_type,
    }

    if _cache["test_mode"]:
        logger.info("Test mode enabled - skipping SQS enqueue")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Test mode - job not enqueued",
                    "job_id": job_id,
                    "run_id": run_id,
                    "test_mode": True,
                }
            ),
        }

    result = await _enqueue_job(job_data)

    if result.get("success"):
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Job enqueued successfully",
                    "job_id": job_id,
                    "run_id": run_id,
                    "message_id": result.get("message_id"),
                }
            ),
        }

    return {
        "statusCode": 500,
        "body": json.dumps(
            {
                "message": "Failed to enqueue job",
                "error": result.get("error"),
                "job_id": job_id,
            }
        ),
    }


def _handle_health_check() -> dict[str, Any]:
    """Handle health check request."""
    health_status = {"status": "healthy", "timestamp": int(time.time())}
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(health_status),
    }


def _parse_event_body(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Parse event body from API Gateway event.

    Returns:
        Tuple of (raw body string, parsed payload)

    Raises:
        ValueError: If body cannot be parsed
    """
    body_str = event.get("body", "")
    if event.get("isBase64Encoded"):
        body_str = base64.b64decode(body_str).decode("utf-8")

    if body_str.startswith("payload="):
        payload_json = unquote(body_str[8:])
        payload = json.loads(payload_json)
    else:
        payload = json.loads(body_str)

    return body_str, payload


async def _verify_webhook_signature(
    body_str: str, signature_header: str | None
) -> dict[str, Any]:
    """Verify webhook signature.

    Returns:
        Error response dict if verification fails, empty dict if successful
    """
    try:
        webhook_secret = await _get_webhook_secret()
        if not _verify_signature(body_str, signature_header or "", webhook_secret):
            logger.error("Webhook signature verification failed")
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid signature"}),
            }
        return {}
    except RuntimeError as err:
        logger.error("Cannot verify signature, secret unavailable: %s", str(err))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Authentication system unavailable"}),
        }


def _get_header_case_insensitive(
    headers: dict[str, str], key: str
) -> str | None:
    """Get header value case-insensitively."""
    lower_key = key.lower()
    for header_name, header_value in (headers or {}).items():
        if header_name.lower() == lower_key:
            return header_value
    return None


async def _process_webhook_event(
    event: dict[str, Any], headers: dict[str, str], start_time: float
) -> dict[str, Any]:
    """Process a webhook event from API Gateway."""
    try:
        body_str, payload = _parse_event_body(event)
    except (json.JSONDecodeError, ValueError) as err:
        logger.error("Failed to parse request body: %s", str(err))
        logger.error(
            "Body content (first 500 chars): %s", str(event.get("body", ""))[:500]
        )
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON payload"}),
        }

    signature_header = _get_header_case_insensitive(headers, "x-hub-signature-256")
    if signature_header:
        error_response = await _verify_webhook_signature(body_str, signature_header)
        if error_response.get("statusCode"):
            return error_response
    else:
        logger.warning("No signature header found, proceeding without verification")

    delivery_id = _get_header_case_insensitive(headers, "x-github-delivery")
    if delivery_id and await _check_and_record_idempotency(delivery_id):
        logger.info("Duplicate webhook delivery detected, returning success")
        elapsed_ms = (time.time() - start_time) * 1000
        _publish_metric("ProcessingTime", elapsed_ms, "Milliseconds")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Duplicate request ignored"}),
        }

    event_type = (
        _get_header_case_insensitive(headers, "x-github-event")
        or payload.get("event_type")
    )
    logger.info("GitHub event type: %s", event_type)
    elapsed_ms = (time.time() - start_time) * 1000
    _publish_metric("ProcessingTime", elapsed_ms, "Milliseconds")

    if event_type == "workflow_job":
        return await _handle_workflow_job(payload)

    if event_type == "workflow_run":
        return _handle_workflow_run(payload)

    if event_type == "ping":
        logger.info("Received ping event")
    else:
        logger.info("Ignoring event type: %s", event_type)

    message = "pong" if event_type == "ping" else f"Event type {event_type} ignored"
    return {"statusCode": 200, "body": json.dumps({"message": message})}


async def _handle_api_gateway_event(
    event: dict[str, Any], start_time: float
) -> dict[str, Any]:
    """Handle an API Gateway event."""
    headers = event.get("headers", {})
    _set_test_mode(_get_header_case_insensitive(headers, "x-test-mode") == "true")

    http_context = event.get("requestContext", {}).get("http", {})
    http_method = event.get("httpMethod") or http_context.get("method", "")
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": (
                    "Content-Type,x-api-key,x-github-event,"
                    "x-hub-signature-256,x-github-delivery"
                ),
            },
            "body": "",
        }

    path = event.get("path") or event.get("rawPath", "")
    if path == "/v1/runners/health":
        return _handle_health_check()

    return await _process_webhook_event(event, headers, start_time)


def _get_ingress_handler() -> IngressHandler:
    """Create an ingress handler with dependencies."""

    class IngressDeps:
        """Dependencies for IngressHandler."""

        async def get_webhook_secret(self) -> str:
            """Get webhook secret from SSM."""
            return await _get_webhook_secret()

        def verify_signature(self, body: str, signature: str, secret: str) -> bool:
            """Verify webhook signature."""
            return _verify_signature(body, signature, secret)

        def publish_metric(self, name: str, value: float, unit: str) -> None:
            """Publish CloudWatch metric."""
            _publish_metric(name, value, unit)

        async def check_idempotency(self, delivery_id: str) -> bool:
            """Check if delivery is duplicate."""
            return await _check_and_record_idempotency(delivery_id)

        def get_runner_type(self, labels: list[str]) -> tuple[str | None, str | None]:
            """Get runner type from labels."""
            return get_runner_type_from_labels(labels)

        async def enqueue_job(self, job_data: dict[str, Any]) -> dict[str, bool]:
            """Enqueue job to SQS."""
            result = await _enqueue_job(job_data)
            return {"success": result.get("success", False)}

        async def enqueue_cancellation(
            self, cancellation_data: dict[str, Any]
        ) -> dict[str, bool]:
            """Enqueue cancellation to SQS."""
            result = await _enqueue_cancellation(cancellation_data)
            return {"success": result.get("success", False)}

        def enqueue_ignored(self, payload: dict[str, Any], reason: str) -> None:
            """Enqueue ignored event to SQS."""
            _enqueue_ignored_event(payload, reason)

    return IngressHandler(IngressDeps())


async def _async_handler(event: dict[str, Any]) -> dict[str, Any]:
    """Async handler implementation."""
    start_time = time.time()
    logger.info("Received event: %s", json.dumps(event))

    records = event.get("Records", [])
    is_sqs = (
        len(records) > 0 and records[0].get("eventSource") == "aws:sqs"
    )

    if is_sqs:
        # This Lambda only handles webhook_ingress queue
        # job_queue is handled by runner_starter Lambda
        # cancellation_queue is handled by runner_terminator Lambda
        logger.info("Processing SQS event from webhook_ingress queue")

        ingress_handler = _get_ingress_handler()
        results = [await ingress_handler.handle(record) for record in records]

        if not all(r.get("success") for r in results):
            raise RuntimeError("One or more webhook_ingress messages failed")

        return {"statusCode": 200, "body": json.dumps({"message": "Processed"})}

    return await _handle_api_gateway_event(event, start_time)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for webhook routing.

    Args:
        event: Lambda event (API Gateway or SQS)
        _context: Lambda context (unused)

    Returns:
        Response dictionary
    """
    return asyncio.get_event_loop().run_until_complete(_async_handler(event))
