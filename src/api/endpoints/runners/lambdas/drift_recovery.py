"""Drift recovery Lambda handler - triggers workflow on infrastructure drift."""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any

from botocore.exceptions import ClientError

from common.aws_clients import get_ec2_client, get_sns_client, get_ssm_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _is_resource_in_managed_vpc(resource_id: str, resource_type: str) -> bool:
    """Check if a resource is in the managed VPC.

    Args:
        resource_id: AWS resource ID
        resource_type: AWS CloudFormation resource type

    Returns:
        True if resource is in managed VPC or no VPC is configured
    """
    managed_vpc_id = os.environ.get("MANAGED_VPC_ID", "")
    if not managed_vpc_id:
        return True

    ec2 = get_ec2_client()
    result = True

    try:
        if resource_type == "AWS::EC2::VPC":
            result = resource_id == managed_vpc_id
        elif resource_type == "AWS::EC2::Subnet":
            response = ec2.describe_subnets(SubnetIds=[resource_id])
            subnets = response.get("Subnets", [])
            result = len(subnets) > 0 and subnets[0].get("VpcId") == managed_vpc_id
        elif resource_type == "AWS::EC2::SecurityGroup":
            response = ec2.describe_security_groups(GroupIds=[resource_id])
            groups = response.get("SecurityGroups", [])
            if groups:
                group = groups[0]
                is_default = group.get("GroupName") == "default"
                is_in_vpc = group.get("VpcId") == managed_vpc_id
                result = is_in_vpc and not is_default
            else:
                result = False
    except ClientError as err:
        logger.warning("Failed to check resource VPC: %s", str(err))
        result = False

    return result


def _get_github_token() -> str:
    """Retrieve GitHub token from SSM Parameter Store.

    Returns:
        GitHub token or empty string if not available
    """
    parameter_name = os.environ.get("GITHUB_TOKEN_PARAMETER_NAME")
    if not parameter_name:
        logger.error("GITHUB_TOKEN_PARAMETER_NAME not set")
        return ""

    try:
        response = get_ssm_client().get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        return response.get("Parameter", {}).get("Value", "")
    except ClientError as err:
        logger.error("Failed to retrieve GitHub token: %s", str(err))
        return ""


def _trigger_api_workflow(github_token: str) -> dict[str, Any]:
    """Trigger the api_backend.yml workflow via GitHub API.

    Args:
        github_token: GitHub personal access token

    Returns:
        Result dictionary with success status
    """
    github_repo = os.environ.get("GITHUB_REPO", "")
    workflow_file = "api_backend.yml"
    url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches"

    payload = {"ref": "main", "inputs": {"github_hosted": "true"}}

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "DriftRecovery/1.0",
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status == 204:
                return {"success": True, "message": "Workflow triggered"}
            return {"success": False, "error": f"Unexpected status: {response.status}"}
    except urllib.error.HTTPError as err:
        logger.error("Failed to trigger workflow: HTTP %d", err.code)
        return {"success": False, "error": f"HTTP {err.code}"}
    except urllib.error.URLError as err:
        logger.error("Failed to trigger workflow: %s", str(err))
        return {"success": False, "error": str(err)}


def _send_notification(subject: str, message: str) -> None:
    """Send notification via SNS.

    Args:
        subject: Notification subject
        message: Notification message body
    """
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if not sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured, skipping notification")
        return

    try:
        get_sns_client().publish(
            TopicArn=sns_topic_arn, Subject=subject, Message=message
        )
        logger.info("Notification sent: %s", subject)
    except ClientError as err:
        logger.error("Failed to send notification: %s", str(err))


def _extract_event_from_sqs(event: dict[str, Any]) -> dict[str, Any]:
    """Extract the actual event from SQS wrapper.

    Args:
        event: Lambda event (may be SQS wrapped)

    Returns:
        Inner event payload
    """
    records = event.get("Records", [])
    if records:
        body = records[0].get("body", "{}")
        return json.loads(body)
    return event


def _format_drift_details(trigger_event: dict[str, Any]) -> dict[str, str]:
    """Format drift event details for logging and notifications.

    Args:
        trigger_event: Config rule trigger event

    Returns:
        Dictionary with formatted drift details
    """
    rule_name = trigger_event.get("configRuleName", "Unknown")
    resource_type = trigger_event.get("resourceType", "Unknown")
    resource_id = trigger_event.get("resourceId", "Unknown")
    aws_region = trigger_event.get("awsRegion", "Unknown")

    return {
        "rule_name": rule_name,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "aws_region": aws_region,
        "summary": f"{resource_type} ({resource_id}) in {aws_region}",
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for drift recovery.

    Args:
        event: Lambda event (SQS message from Config rule)
        _context: Lambda context (unused)

    Returns:
        Response dictionary with status
    """
    logger.info("Received SQS event: %s", json.dumps(event))
    trigger_event = _extract_event_from_sqs(event)
    drift = _format_drift_details(trigger_event)
    logger.info("Drift detected: %s", drift["summary"])

    is_in_managed_vpc = _is_resource_in_managed_vpc(
        drift["resource_id"], drift["resource_type"]
    )
    if not is_in_managed_vpc:
        logger.info("Resource %s is not in managed VPC, skipping", drift["resource_id"])
        return {"statusCode": 200, "body": "Resource not in managed VPC, skipping"}

    github_repo = os.environ.get("GITHUB_REPO", "")
    github_token = _get_github_token()

    if not github_token:
        error_msg = "Failed to retrieve GitHub token"
        logger.error(error_msg)
        _send_notification(
            f"Drift Recovery FAILED: {drift['rule_name']}",
            f"Infrastructure drift was detected.\n\n"
            f"Resource: {drift['summary']}\n"
            f"Rule: {drift['rule_name']}\n\n"
            f"FAILED to trigger recovery workflow: {error_msg}\n\n"
            f"MANUAL INTERVENTION REQUIRED",
        )
        return {"statusCode": 500, "body": error_msg}

    result = _trigger_api_workflow(github_token)

    if result.get("success"):
        logger.info("Successfully triggered api_backend.yml workflow for drift recovery")
        _send_notification(
            f"Drift Recovery Triggered: {drift['rule_name']}",
            f"Infrastructure drift was detected.\n\n"
            f"Resource: {drift['summary']}\n"
            f"Rule: {drift['rule_name']}\n\n"
            f"Automatically triggered api_backend.yml workflow "
            f"to recover infrastructure.\n\n"
            f"Monitor the workflow at: https://github.com/{github_repo}/actions",
        )
        return {"statusCode": 200, "body": "Recovery workflow triggered"}

    logger.error("Failed to trigger workflow: %s", result.get("error"))
    _send_notification(
        f"Drift Recovery FAILED: {drift['rule_name']}",
        f"Infrastructure drift was detected.\n\n"
        f"Resource: {drift['summary']}\n"
        f"Rule: {drift['rule_name']}\n\n"
        f"FAILED to trigger recovery workflow: {result.get('error')}\n\n"
        f"MANUAL INTERVENTION REQUIRED",
    )
    return {"statusCode": 500, "body": "Failed to trigger recovery"}
