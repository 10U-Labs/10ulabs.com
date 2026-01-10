"""Lambda handler for circuit breaker status and reset."""

import json
import logging
import os
from typing import Any

from botocore.exceptions import ClientError

from common.circuit_breaker_utils import (
    enable_event_source_mappings,
    get_dynamodb_client,
    get_lambda_client,
    reset_circuit_breaker_state,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_circuit_breaker_status(
    webhook_function_name: str, state_table_name: str
) -> dict[str, Any]:
    """Get current circuit breaker status."""
    dynamodb = get_dynamodb_client()
    lambda_client = get_lambda_client()

    # Get DynamoDB state
    try:
        response = dynamodb.get_item(
            TableName=state_table_name, Key={"state_id": {"S": "current"}}
        )
        item = response.get("Item", {})
        db_state = item.get("state", {}).get("S", "unknown")
        last_failure = int(item.get("last_failure_time", {}).get("N", "0"))
        recovery_attempts = int(item.get("recovery_attempts", {}).get("N", "0"))
    except ClientError as e:
        logger.error("Failed to get DynamoDB state: %s", e)
        db_state = "error"
        last_failure = 0
        recovery_attempts = 0

    # Get event source mapping state
    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=webhook_function_name
        )
        mappings = response.get("EventSourceMappings", [])
        sqs_state = mappings[0]["State"] if mappings else "no_mapping"
    except ClientError as e:
        logger.error("Failed to get event source state: %s", e)
        sqs_state = "error"

    # Get reserved concurrency
    try:
        response = lambda_client.get_function_concurrency(
            FunctionName=webhook_function_name
        )
        concurrency = response.get("ReservedConcurrentExecutions")
    except lambda_client.exceptions.ResourceNotFoundException:
        concurrency = None
    except ClientError as e:
        logger.error("Failed to get concurrency: %s", e)
        concurrency = "error"

    # Determine overall health
    is_healthy = (
        db_state == "closed"
        and sqs_state == "Enabled"
        and concurrency is None
    )

    return {
        "healthy": is_healthy,
        "state": db_state,
        "sqs_event_source": sqs_state,
        "reserved_concurrency": concurrency,
        "last_failure_time": last_failure,
        "recovery_attempts": recovery_attempts,
    }


def remove_lambda_reserved_concurrency(function_name: str) -> dict[str, Any]:
    """Remove reserved concurrency limit from a Lambda function."""
    lambda_client = get_lambda_client()

    try:
        lambda_client.delete_function_concurrency(FunctionName=function_name)
        logger.info("Removed reserved concurrency for %s", function_name)
        return {"success": True, "message": "Removed reserved concurrency limit"}
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info("No reserved concurrency to remove for %s", function_name)
        return {"success": True, "message": "No reserved concurrency was set"}
    except ClientError as e:
        logger.error("Failed to remove reserved concurrency: %s", e)
        return {"success": False, "error": str(e)}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Handle circuit breaker API requests.

    GET  /v1/runners/circuit-breaker - Get status
    POST /v1/runners/circuit-breaker - Reset circuit breaker
    """
    webhook_function_name = os.environ["WEBHOOK_FUNCTION_NAME"]
    state_table_name = os.environ["STATE_TABLE_NAME"]

    http_method = event.get("httpMethod", "GET")

    if http_method == "GET":
        logger.info("Getting circuit breaker status")
        status = get_circuit_breaker_status(webhook_function_name, state_table_name)
        return {
            "statusCode": 200 if status["healthy"] else 503,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(status),
        }

    if http_method == "POST":
        logger.info("Resetting circuit breaker for %s", webhook_function_name)

        results = {
            "state_reset": reset_circuit_breaker_state(state_table_name),
            "concurrency_removed": remove_lambda_reserved_concurrency(
                webhook_function_name
            ),
            "sqs_enabled": enable_event_source_mappings(webhook_function_name),
        }

        all_success = all(r.get("success", False) for r in results.values())

        response_body = {
            "success": all_success,
            "message": "Circuit breaker reset" if all_success else "Partial failure",
            "details": results,
        }

        return {
            "statusCode": 200 if all_success else 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(response_body),
        }

    return {
        "statusCode": 405,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": "Method not allowed"}),
    }
