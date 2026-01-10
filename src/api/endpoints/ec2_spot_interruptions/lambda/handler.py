"""EC2 spot interruption handler - detects spot interruptions and triggers retries.

This endpoint receives EC2 spot interruption warning events from EventBridge
and sends retry requests to the github-workflows/retries queue for runners
that have workflow metadata in their tags.
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_ec2_client():
    """Get EC2 client."""
    return boto3.client("ec2")


def _get_sqs_client():
    """Get SQS client."""
    return boto3.client("sqs")


def _get_ec2_instance_tags(instance_id: str) -> dict[str, str]:
    """Get tags from an EC2 instance.

    Args:
        instance_id: EC2 instance ID

    Returns:
        Dictionary of tag key-value pairs
    """
    tag_dict: dict[str, str] = {}
    try:
        response = _get_ec2_client().describe_instances(InstanceIds=[instance_id])
        reservations = response.get("Reservations", [])
        if reservations:
            instances = reservations[0].get("Instances", [])
            if instances:
                tags = instances[0].get("Tags", [])
                for tag in tags:
                    tag_dict[tag["Key"]] = tag["Value"]
    except ClientError as err:
        logger.error("Failed to get instance tags: %s", str(err))
    return tag_dict


def _send_retry_request(
    run_id: int,
    github_repo: str,
    reason: str,
    resource_type: str,
    resource_id: str,
) -> bool:
    """Send a retry request to the github-workflows/retries queue.

    Args:
        run_id: GitHub workflow run ID
        github_repo: Repository full name (org/repo)
        reason: Reason for the retry
        resource_type: Type of resource (ec2)
        resource_id: Resource identifier (instance ID)

    Returns:
        True if message sent successfully
    """
    queue_url = os.environ.get("RETRIES_QUEUE_URL", "")
    if not queue_url:
        logger.error("RETRIES_QUEUE_URL not set")
        return False

    message = {
        "run_id": run_id,
        "github_repo": github_repo,
        "reason": reason,
        "resource_type": resource_type,
        "resource_id": resource_id,
    }

    try:
        _get_sqs_client().send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )
        logger.info("Sent retry request for run_id=%s to queue", run_id)
        return True
    except ClientError as err:
        logger.error("Failed to send retry request: %s", str(err))
        return False


def _handle_ec2_spot_interruption(event: dict[str, Any]) -> dict[str, Any]:
    """Handle EC2 spot interruption warning.

    Args:
        event: EventBridge event

    Returns:
        Response dictionary
    """
    instance_id = event.get("detail", {}).get("instance-id", "")
    logger.info("EC2 spot interruption warning for instance: %s", instance_id)

    if not instance_id:
        logger.error("No instance-id in event")
        return {"statusCode": 400, "body": json.dumps({"error": "No instance-id"})}

    tag_dict = _get_ec2_instance_tags(instance_id)
    if not tag_dict:
        logger.warning("No tags found for instance %s", instance_id)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No tags found", "handled": False}),
        }

    run_id_str = tag_dict.get("RunId", "")
    github_repo = tag_dict.get("GitHubRepo", "")

    if not run_id_str or not github_repo:
        logger.info("Instance %s is not a runner (no RunId/GitHubRepo tags)", instance_id)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Not our runner", "handled": False}),
        }

    reason = f"EC2 spot instance {instance_id} received interruption warning"
    if _send_retry_request(
        run_id=int(run_id_str),
        github_repo=github_repo,
        reason=reason,
        resource_type="ec2",
        resource_id=instance_id,
    ):
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Retry request sent",
                "handled": True,
                "instance_id": instance_id,
                "run_id": run_id_str,
            }),
        }

    return {
        "statusCode": 500,
        "body": json.dumps({"error": "Failed to send retry request"}),
    }


def _process_sqs_record(record: dict[str, Any]) -> dict[str, Any]:
    """Process a single SQS record containing an EventBridge event.

    Args:
        record: SQS record

    Returns:
        Response dictionary
    """
    body = json.loads(record["body"])

    # Check if this is a direct EventBridge event or wrapped
    if "source" in body and "detail-type" in body:
        return _handle_ec2_spot_interruption(body)

    # Otherwise assume it's the event body directly
    return _handle_ec2_spot_interruption(body)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for EC2 spot interruption events.

    Handles both direct EventBridge invocations and SQS-triggered events.

    Args:
        event: EventBridge event or SQS event
        _context: Lambda context (unused)

    Returns:
        Response dictionary
    """
    logger.info("Received event: %s", json.dumps(event))

    # Handle SQS event
    if "Records" in event:
        results = []
        for record in event["Records"]:
            result = _process_sqs_record(record)
            results.append(result)
        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}),
        }

    # Handle direct EventBridge invocation
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    if source == "aws.ec2" and detail_type == "EC2 Spot Instance Interruption Warning":
        return _handle_ec2_spot_interruption(event)

    logger.info("Ignoring event: source=%s, detail-type=%s", source, detail_type)
    return {"statusCode": 200, "body": json.dumps({"message": "Event ignored"})}
