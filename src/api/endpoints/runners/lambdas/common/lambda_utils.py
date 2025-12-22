"""Common Lambda handler utilities."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_sqs_records(event: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Extract SQS records from Lambda event, returning None if empty.

    Args:
        event: Lambda event with SQS records

    Returns:
        List of SQS records, or None if no records
    """
    logger.info("Received event: %s", json.dumps(event))
    records = event.get("Records", [])
    if not records:
        logger.warning("No records in event")
        return None
    return records


def empty_records_response() -> dict[str, Any]:
    """Return standard response for empty records.

    Returns:
        Standard 200 response indicating no records to process
    """
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "No records to process"}),
    }


def count_results(results: list[dict[str, Any]]) -> tuple[int, int]:
    """Count successful and failed results.

    Args:
        results: List of result dictionaries with 'success' key

    Returns:
        Tuple of (success_count, fail_count)
    """
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = sum(1 for r in results if not r.get("success"))
    return success_count, fail_count


def parse_error_response(err: Exception) -> dict[str, Any]:
    """Create standardized error response for message parsing failures.

    Args:
        err: The exception that occurred during parsing

    Returns:
        Error response dictionary
    """
    logger.error("Failed to parse message: %s", str(err))
    return {"success": False, "error": f"Parse error: {err}"}
