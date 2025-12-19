"""Archive ignored webhook events to S3."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.cloudwatch import publish_metric

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METRICS_NAMESPACE = "IgnoredEventsArchiver"

_cache: dict[str, Any] = {"s3_client": None}


def _get_s3_client() -> Any:
    """Get or create S3 client (singleton)."""
    if _cache["s3_client"] is None:
        _cache["s3_client"] = boto3.client("s3")
    return _cache["s3_client"]


def _build_s3_key(timestamp: str, message_id: str) -> str:
    """Build S3 key for archived event.

    Args:
        timestamp: ISO format timestamp
        message_id: SQS message ID

    Returns:
        S3 key path like ignored-events/2024/01/15/12/message-id.json
    """
    try:
        date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        date = datetime.now(timezone.utc)

    year = date.year
    month = f"{date.month:02d}"
    day = f"{date.day:02d}"
    hour = f"{date.hour:02d}"

    return f"ignored-events/{year}/{month}/{day}/{hour}/{message_id}.json"


def _archive_event(record: dict[str, Any]) -> dict[str, Any]:
    """Archive a single SQS record to S3.

    Args:
        record: SQS record dictionary

    Returns:
        Result dictionary with success status and key or error
    """
    bucket_name = os.environ.get("ARCHIVE_BUCKET_NAME")
    if not bucket_name:
        logger.error("ARCHIVE_BUCKET_NAME not set")
        return {"success": False, "error": "Archive bucket not configured"}

    try:
        body = json.loads(record.get("body", "{}"))
        timestamp = body.get("timestamp", datetime.now(timezone.utc).isoformat())
        message_id = record.get("messageId", "unknown")

        archived_event = {
            "message_id": message_id,
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "original_timestamp": timestamp,
            "event_data": body.get("event_data"),
            "reason": body.get("reason"),
            "sqs_attributes": record.get("attributes", {}),
        }

        s3_key = _build_s3_key(timestamp, message_id)

        _get_s3_client().put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(archived_event, indent=2),
            ContentType="application/json",
        )

        logger.info("Archived event to S3: %s", s3_key)
        return {"success": True, "key": s3_key}
    except (json.JSONDecodeError, ClientError) as err:
        logger.error("Failed to archive event: %s", str(err))
        return {"success": False, "error": str(err)}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for archiving ignored events.

    Args:
        event: Lambda event with SQS records
        _context: Lambda context (unused)

    Returns:
        Response dictionary with status and counts

    Raises:
        RuntimeError: If any events fail to archive
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

    logger.info("Archiving %d ignored event(s) to S3", len(records))

    results = [_archive_event(record) for record in records]

    elapsed_ms = (time.time() - start_time) * 1000
    publish_metric(METRICS_NAMESPACE, "ProcessingTime", elapsed_ms, "Milliseconds")

    success_count = sum(1 for r in results if r.get("success"))
    fail_count = sum(1 for r in results if not r.get("success"))

    publish_metric(METRICS_NAMESPACE, "EventsArchived", float(success_count), "Count")

    logger.info("Archived %d event(s) successfully, %d failed", success_count, fail_count)

    if fail_count > 0:
        publish_metric(METRICS_NAMESPACE, "ArchiveErrors", float(fail_count), "Count")
        raise RuntimeError(f"{fail_count} event(s) failed to archive")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Archived",
                "count": len(records),
                "success": success_count,
                "failed": fail_count,
            }
        ),
    }
