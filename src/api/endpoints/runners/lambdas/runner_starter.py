"""Runner starter Lambda handler - routes job requests to runner APIs."""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.cloudwatch import publish_metric
from common.runner_labels import (
    parse_labels,
    validate_labels,
    LabelParseError,
    LabelValidationError,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METRICS_NAMESPACE = "RunnerStarter"

_cache: dict[str, Any] = {"ssm_client": None, "api_key": None}

_circuit_breaker_state: dict[str, Any] = {
    "failures": 0,
    "last_failure_time": 0.0,
    "state": "closed",
}


def _get_ssm_client() -> Any:
    """Get or create SSM client (singleton)."""
    if _cache["ssm_client"] is None:
        _cache["ssm_client"] = boto3.client("ssm")
    return _cache["ssm_client"]


def _check_circuit_breaker() -> bool:
    """Check if requests should be allowed through the circuit breaker.

    Returns:
        True if requests should proceed, False if circuit is open
    """
    current_time = time.time()
    failure_threshold = 5
    timeout_seconds = 60

    if _circuit_breaker_state["state"] == "open":
        if current_time - _circuit_breaker_state["last_failure_time"] > timeout_seconds:
            logger.info("Circuit breaker transitioning to half-open state")
            _circuit_breaker_state["state"] = "half-open"
            _circuit_breaker_state["failures"] = 0
            publish_metric(METRICS_NAMESPACE, "CircuitBreakerState", 1.0, "Count")
            return True
        publish_metric(METRICS_NAMESPACE, "CircuitBreakerState", 2.0, "Count")
        return False

    if _circuit_breaker_state["failures"] >= failure_threshold:
        logger.warning(
            "Circuit breaker opening due to %d failures",
            _circuit_breaker_state["failures"],
        )
        _circuit_breaker_state["state"] = "open"
        _circuit_breaker_state["last_failure_time"] = current_time
        publish_metric(METRICS_NAMESPACE, "CircuitBreakerState", 2.0, "Count")
        return False

    publish_metric(METRICS_NAMESPACE, "CircuitBreakerState", 0.0, "Count")
    return True


def _record_circuit_breaker_success() -> None:
    """Record a successful request for the circuit breaker."""
    if _circuit_breaker_state["state"] == "half-open":
        logger.info("Circuit breaker closing after successful request")
        _circuit_breaker_state["state"] = "closed"
    _circuit_breaker_state["failures"] = 0


def _record_circuit_breaker_failure() -> None:
    """Record a failed request for the circuit breaker."""
    _circuit_breaker_state["failures"] += 1
    _circuit_breaker_state["last_failure_time"] = time.time()
    if _circuit_breaker_state["state"] == "half-open":
        logger.warning(
            "Circuit breaker reopening after failed request in half-open state"
        )
        _circuit_breaker_state["state"] = "open"


def _should_record_circuit_breaker_failure(status_code: int | None) -> bool:
    """Check if a status code should count as a circuit breaker failure."""
    return status_code is None


def _get_api_key(force_refresh: bool = False) -> str:
    """Get API key from SSM Parameter Store with caching.

    Args:
        force_refresh: Force refresh of cached key

    Returns:
        API key string

    Raises:
        RuntimeError: If API key cannot be retrieved
    """
    if force_refresh:
        _cache["api_key"] = None

    if _cache["api_key"]:
        return _cache["api_key"]

    parameter_name = os.environ.get("API_KEY_PARAMETER_NAME")
    if not parameter_name:
        raise RuntimeError("API_KEY_PARAMETER_NAME environment variable not set")

    try:
        response = _get_ssm_client().get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        api_key = response.get("Parameter", {}).get("Value", "")
        _cache["api_key"] = api_key
        return api_key
    except ClientError as err:
        logger.error("Failed to retrieve API key: %s", str(err))
        raise RuntimeError(f"Cannot retrieve API key: {err}") from err


def _make_http_request_with_retry(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    max_retries: int = 3,
) -> tuple[bool, dict[str, Any] | None, str | None, int | None]:
    """Make HTTP POST request with exponential backoff retry.

    Args:
        endpoint: Full URL to POST to
        payload: JSON payload
        headers: Additional headers
        max_retries: Maximum retry attempts

    Returns:
        Tuple of (success, response_data, error, status_code)
    """
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    last_status_code: int | None = None

    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=request_headers,
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                last_status_code = response.status
                if 200 <= response.status < 300:
                    response_body = response.read().decode("utf-8")
                    response_data = json.loads(response_body) if response_body else {}
                    return True, response_data, None, response.status
        except urllib.error.HTTPError as err:
            last_status_code = err.code
            if 400 <= err.code < 500:
                return False, None, f"HTTP {err.code}", err.code
            if attempt >= max_retries:
                return (
                    False,
                    None,
                    f"HTTP {err.code} after {max_retries + 1} attempts",
                    err.code,
                )
        except urllib.error.URLError as err:
            if attempt >= max_retries:
                return (
                    False,
                    None,
                    f"{err.reason} after {max_retries + 1} attempts",
                    last_status_code,
                )

        # Exponential backoff
        time.sleep(2**attempt)

    return False, None, "Max retries exceeded", last_status_code


def _get_runner_type_from_labels(
    job_labels: list[str],
) -> tuple[str | None, str | None]:
    """Determine runner type and endpoint suffix from job labels.

    Args:
        job_labels: List of job labels

    Returns:
        Tuple of (runner_type, endpoint_suffix)
    """
    runner_type: str | None = None
    endpoint_suffix: str | None = None

    try:
        parsed = parse_labels(job_labels)
        validate_labels(parsed)
        is_e2e = "e2e" in job_labels

        if parsed["platform"] == "ec2":
            runner_type = "ec2-e2e" if is_e2e else "ec2"
            endpoint_suffix = "ec2-runner"
        elif parsed["platform"] == "ecs":
            runner_type = "fargate-e2e" if is_e2e else "fargate"
            endpoint_suffix = "ecs-runner"
    except (LabelParseError, LabelValidationError):
        pass

    return runner_type, endpoint_suffix


def _build_runner_endpoint(endpoint_suffix: str) -> str:
    """Build full runner endpoint URL."""
    base_url = os.environ.get("API_BASE_URL", "")
    return f"{base_url}/v1/{endpoint_suffix}"


def _handle_route_success(
    job_id: int, runner_type: str, response_data: dict[str, Any] | None
) -> dict[str, Any]:
    """Handle successful route request."""
    logger.info("Successfully routed job %s to %s runner", job_id, runner_type)
    _record_circuit_breaker_success()
    return {"success": True, "runner_type": runner_type, "response": response_data}


def _handle_route_failure(
    job_id: int, error: str | None, status_code: int | None
) -> dict[str, Any]:
    """Handle failed route request."""
    logger.error("Failed to route job %s: %s", job_id, error)
    if _should_record_circuit_breaker_failure(status_code):
        _record_circuit_breaker_failure()
    else:
        logger.warning(
            "Status %s for job %s - not counting as circuit breaker failure",
            status_code,
            job_id,
        )
    return {"success": False, "error": error}


def _route_runner_request(
    job_id: int,
    job_labels: list[str],
    github_repo: str,
    run_id: int | None = None,
) -> dict[str, Any]:
    """Route a job request to the appropriate runner API.

    Args:
        job_id: GitHub job ID
        job_labels: Job labels
        github_repo: Repository full name
        run_id: Optional workflow run ID

    Returns:
        Result dictionary with success status
    """
    if not _check_circuit_breaker():
        logger.error("Circuit breaker is open, rejecting request for job %s", job_id)
        return {
            "success": False,
            "error": "Service temporarily unavailable (circuit breaker open)",
        }

    runner_type, endpoint_suffix = _get_runner_type_from_labels(job_labels)
    if not runner_type or not endpoint_suffix:
        logger.error("No matching runner type for labels: %s", job_labels)
        return {
            "success": False,
            "error": f"No matching runner type for labels: {json.dumps(job_labels)}",
        }

    try:
        api_key = _get_api_key()
    except RuntimeError as err:
        logger.error("Cannot route job %s: %s", job_id, str(err))
        return {"success": False, "error": str(err)}

    endpoint = _build_runner_endpoint(endpoint_suffix)
    payload = {
        "job_id": job_id,
        "job_labels": job_labels,
        "github_repo": github_repo,
        "run_id": run_id,
        "runner_type": runner_type,
    }

    logger.info(
        "Routing job %s to %s runner: %s (run_id=%s)",
        job_id,
        runner_type,
        endpoint,
        run_id,
    )

    success, response_data, error, status_code = _make_http_request_with_retry(
        endpoint, payload, {"x-api-key": api_key}
    )

    if success:
        return _handle_route_success(job_id, runner_type, response_data)
    return _handle_route_failure(job_id, error, status_code)


def _handle_sqs_message(message: dict[str, Any]) -> dict[str, Any]:
    """Handle a single SQS message.

    Args:
        message: SQS message record

    Returns:
        Result dictionary with success status
    """
    try:
        body = json.loads(message.get("body", "{}"))
        job_id = body.get("job_id")
        job_labels = body.get("job_labels", [])
        github_repo = body.get("github_repo")
        run_id = body.get("run_id")

        logger.info(
            "Processing job from SQS: job_id=%s, labels=%s, repo=%s, run_id=%s",
            job_id,
            json.dumps(job_labels),
            github_repo,
            run_id,
        )

        result = _route_runner_request(job_id, job_labels, github_repo, run_id)

        if result.get("success"):
            logger.info("Successfully processed SQS message for job %s", job_id)
            return {"success": True}

        logger.error(
            "Failed to process SQS message for job %s: %s",
            job_id,
            result.get("error"),
        )
        return {"success": False, "error": result.get("error")}
    except (json.JSONDecodeError, KeyError) as err:
        logger.error("Failed to parse SQS message: %s", str(err))
        return {"success": False, "error": f"Invalid message format: {err}"}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for runner starter.

    Args:
        event: Lambda event with SQS records
        _context: Lambda context (unused)

    Returns:
        Response dictionary with status

    Raises:
        RuntimeError: If any job messages fail
    """
    start_time = time.time()
    logger.info("Received event: %s", json.dumps(event))

    records = event.get("Records", [])
    if not records:
        logger.warning("No records in event")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No records to process"}),
        }

    logger.info("Processing %d job(s) from SQS", len(records))

    results = [_handle_sqs_message(record) for record in records]

    elapsed_ms = (time.time() - start_time) * 1000
    publish_metric(METRICS_NAMESPACE, "ProcessingTime", elapsed_ms, "Milliseconds")

    if not all(r.get("success") for r in results):
        raise RuntimeError("One or more job messages failed")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Processed", "count": len(records)}),
    }
