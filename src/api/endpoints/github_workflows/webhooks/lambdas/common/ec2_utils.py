"""EC2 instance utilities for Lambda handlers."""

import logging
from typing import Any

from botocore.exceptions import ClientError

from common.aws_clients import get_ec2_client

logger = logging.getLogger(__name__)


def terminate_ec2_instance(instance_id: str) -> bool:
    """Terminate an EC2 instance with standard error handling.

    Args:
        instance_id: ID of the instance to terminate

    Returns:
        True if successfully terminated or already terminated/not found
    """
    try:
        get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        return True
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        if error_code in ("InvalidInstanceID.NotFound", "InvalidInstanceID.Malformed"):
            logger.info("Instance already terminated or not found: %s", instance_id)
            return True
        logger.error("Failed to terminate EC2 instance: %s", str(err))
        return False


def find_instances_by_tags(
    filters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find EC2 instances by tag filters.

    Args:
        filters: List of EC2 filter dictionaries

    Returns:
        List of instance dictionaries
    """
    instances: list[dict[str, Any]] = []
    try:
        response = get_ec2_client().describe_instances(Filters=filters)
        for reservation in response.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))
    except ClientError as err:
        logger.error("Failed to find instances: %s", str(err))
    return instances
