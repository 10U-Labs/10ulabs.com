"""Circuit breaker utilities for Lambda handlers."""

import logging
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_lambda_client() -> Any:
    """Get Lambda client."""
    return boto3.client("lambda")


def get_dynamodb_client() -> Any:
    """Get DynamoDB client."""
    return boto3.client("dynamodb")


def update_event_source_mappings(
    function_name: str, enable: bool
) -> dict[str, Any]:
    """Enable or disable SQS event source mappings for a Lambda function.

    Args:
        function_name: Lambda function name
        enable: True to enable, False to disable

    Returns:
        Result dictionary with success status and count
    """
    lambda_client = get_lambda_client()
    action = "Enabled" if enable else "Disabled"
    target_state = "Disabled" if enable else "Enabled"
    count_key = "enabled_count" if enable else "disabled_count"

    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=function_name
        )

        updated_count = 0
        for mapping in response.get("EventSourceMappings", []):
            if mapping["State"] == target_state:
                lambda_client.update_event_source_mapping(
                    UUID=mapping["UUID"],
                    Enabled=enable
                )
                logger.info("%s event source mapping: %s", action, mapping["UUID"])
                updated_count += 1

        return {
            "success": True,
            count_key: updated_count,
            "message": f"{action} {updated_count} event source mappings",
        }
    except ClientError as err:
        logger.error("Failed to %s event source mappings: %s", action.lower(), err)
        return {"success": False, "error": str(err)}


def enable_event_source_mappings(function_name: str) -> dict[str, Any]:
    """Enable SQS event source mappings for a Lambda function.

    Args:
        function_name: Lambda function name

    Returns:
        Result dictionary with success status and enabled_count
    """
    return update_event_source_mappings(function_name, enable=True)


def disable_event_source_mappings(function_name: str) -> dict[str, Any]:
    """Disable SQS event source mappings for a Lambda function.

    Args:
        function_name: Lambda function name

    Returns:
        Result dictionary with success status and disabled_count
    """
    return update_event_source_mappings(function_name, enable=False)


def update_circuit_breaker_state(
    table_name: str,
    state: str,
    recovery_attempts: int = 0,
) -> dict[str, Any]:
    """Update circuit breaker state in DynamoDB.

    Args:
        table_name: DynamoDB table name
        state: Circuit breaker state (open, half-open, closed)
        recovery_attempts: Number of recovery attempts

    Returns:
        Result dictionary with success status
    """
    dynamodb = get_dynamodb_client()
    current_time = int(time.time())

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "state_id": {"S": "current"},
                "state": {"S": state},
                "recovery_attempts": {"N": str(recovery_attempts)},
                "last_recovery_attempt": {"N": str(current_time)},
                "last_failure_time": {"N": str(current_time)},
                "ttl": {"N": str(current_time + 2592000)},
            },
        )
        logger.info("Updated circuit breaker state to: %s", state)
        return {"success": True}
    except ClientError as err:
        logger.error("Failed to update circuit breaker state: %s", err)
        return {"success": False, "error": str(err)}
