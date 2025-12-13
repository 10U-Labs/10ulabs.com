"""Lambda handler for circuit breaker status and reset."""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_circuit_breaker_status(
    webhook_function_name: str, state_table_name: str
) -> dict:
    """Get current circuit breaker status."""
    dynamodb = boto3.client("dynamodb")
    lambda_client = boto3.client("lambda")

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


def enable_sqs_event_source(lambda_function_name: str) -> dict:
    """Enable SQS event source mappings for a Lambda function."""
    lambda_client = boto3.client("lambda")

    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=lambda_function_name
        )

        enabled_count = 0
        for mapping in response.get("EventSourceMappings", []):
            if mapping["State"] in ("Disabled", "Disabling"):
                lambda_client.update_event_source_mapping(
                    UUID=mapping["UUID"], Enabled=True
                )
                logger.info("Enabled event source mapping: %s", mapping["UUID"])
                enabled_count += 1

        return {
            "success": True,
            "enabled_count": enabled_count,
            "message": f"Enabled {enabled_count} event source mappings",
        }
    except ClientError as e:
        logger.error("Failed to enable event source mappings: %s", e)
        return {"success": False, "error": str(e)}


def remove_lambda_reserved_concurrency(function_name: str) -> dict:
    """Remove reserved concurrency limit from a Lambda function."""
    lambda_client = boto3.client("lambda")

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


def reset_circuit_breaker_state(table_name: str) -> dict:
    """Reset circuit breaker state to closed in DynamoDB."""
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "state_id": {"S": "current"},
                "state": {"S": "closed"},
                "recovery_attempts": {"N": "0"},
                "last_failure_time": {"N": "0"},
                "last_recovery_attempt": {"N": "0"},
            },
        )
        logger.info("Reset circuit breaker state to closed in %s", table_name)
        return {"success": True, "message": "Circuit breaker state reset to closed"}
    except ClientError as e:
        logger.error("Failed to reset circuit breaker state: %s", e)
        return {"success": False, "error": str(e)}


def lambda_handler(event: dict, _context) -> dict:
    """Handle circuit breaker API requests.

    GET  /v1/runners/circuit-breaker - Get status
    POST /v1/runners/circuit-breaker/reset - Reset circuit breaker
    """
    webhook_function_name = os.environ["WEBHOOK_FUNCTION_NAME"]
    state_table_name = os.environ["STATE_TABLE_NAME"]

    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "")

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

    if http_method == "POST" and "reset" in path:
        logger.info("Resetting circuit breaker for %s", webhook_function_name)

        results = {
            "state_reset": reset_circuit_breaker_state(state_table_name),
            "concurrency_removed": remove_lambda_reserved_concurrency(
                webhook_function_name
            ),
            "sqs_enabled": enable_sqs_event_source(webhook_function_name),
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
