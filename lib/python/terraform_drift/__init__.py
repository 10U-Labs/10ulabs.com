"""
Terraform drift detection module.

This module provides functions to detect when AWS resources exist but are not
in Terraform state. This catches scenarios where:
- Resources were created manually outside of Terraform
- Terraform state was lost or corrupted
- Resources exist from a previous deployment that wasn't imported

Example usage:
    from terraform_drift import check_resource_exists, get_planned_creates

    # Check if a specific resource exists
    exists = check_resource_exists('aws_lambda_function', 'MyFunction', 'us-east-2')

    # Get all resources terraform plans to create
    creates = get_planned_creates('/path/to/terraform/dir')
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, cast

import boto3
from botocore.exceptions import ClientError


# Type alias for resource checker functions
ResourceChecker = Callable[[Any, str], bool]


def _check_lambda(client: Any, name: str) -> bool:
    """Check if Lambda function exists."""
    try:
        client.get_function(FunctionName=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_iam_role(client: Any, name: str) -> bool:
    """Check if IAM role exists."""
    try:
        client.get_role(RoleName=name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def _check_log_group(client: Any, name: str) -> bool:
    """Check if CloudWatch log group exists."""
    response = client.describe_log_groups(logGroupNamePrefix=name, limit=1)
    for group in response.get("logGroups", []):
        if group.get("logGroupName") == name:
            return True
    return False


def _check_dynamodb_table(client: Any, name: str) -> bool:
    """Check if DynamoDB table exists."""
    try:
        client.describe_table(TableName=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_s3_bucket(client: Any, name: str) -> bool:
    """Check if S3 bucket exists."""
    try:
        client.head_bucket(Bucket=name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def _check_sqs_queue(client: Any, name: str) -> bool:
    """Check if SQS queue exists."""
    try:
        client.get_queue_url(QueueName=name)
        return True
    except client.exceptions.QueueDoesNotExist:
        return False


def _check_sns_topic(client: Any, arn: str) -> bool:
    """Check if SNS topic exists (requires full ARN)."""
    try:
        client.get_topic_attributes(TopicArn=arn)
        return True
    except client.exceptions.NotFoundException:
        return False


def _check_ssm_parameter(client: Any, name: str) -> bool:
    """Check if SSM parameter exists."""
    try:
        client.get_parameter(Name=name)
        return True
    except client.exceptions.ParameterNotFound:
        return False


def _check_secretsmanager_secret(client: Any, name: str) -> bool:
    """Check if Secrets Manager secret exists."""
    try:
        client.describe_secret(SecretId=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_eventbridge_rule(client: Any, name: str) -> bool:
    """Check if EventBridge rule exists."""
    try:
        client.describe_rule(Name=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_api_gateway_rest_api(client: Any, api_id: str) -> bool:
    """Check if API Gateway REST API exists."""
    try:
        client.get_rest_api(restApiId=api_id)
        return True
    except client.exceptions.NotFoundException:
        return False


# Registry mapping Terraform resource types to their checker functions
RESOURCE_CHECKERS: Dict[str, ResourceChecker] = {
    "aws_lambda_function": _check_lambda,
    "aws_iam_role": _check_iam_role,
    "aws_cloudwatch_log_group": _check_log_group,
    "aws_dynamodb_table": _check_dynamodb_table,
    "aws_s3_bucket": _check_s3_bucket,
    "aws_sqs_queue": _check_sqs_queue,
    "aws_sns_topic": _check_sns_topic,
    "aws_ssm_parameter": _check_ssm_parameter,
    "aws_secretsmanager_secret": _check_secretsmanager_secret,
    "aws_cloudwatch_event_rule": _check_eventbridge_rule,
    "aws_api_gateway_rest_api": _check_api_gateway_rest_api,
}

# Mapping from Terraform resource type to boto3 client name
RESOURCE_TO_CLIENT: Dict[str, str] = {
    "aws_lambda_function": "lambda",
    "aws_iam_role": "iam",
    "aws_cloudwatch_log_group": "logs",
    "aws_dynamodb_table": "dynamodb",
    "aws_s3_bucket": "s3",
    "aws_sqs_queue": "sqs",
    "aws_sns_topic": "sns",
    "aws_ssm_parameter": "ssm",
    "aws_secretsmanager_secret": "secretsmanager",
    "aws_cloudwatch_event_rule": "events",
    "aws_api_gateway_rest_api": "apigateway",
}


def get_supported_resource_types() -> List[str]:
    """Get list of resource types that can be checked for drift."""
    return list(RESOURCE_CHECKERS.keys())


def check_resource_exists(
    resource_type: str,
    resource_name: str,
    region: str = "us-east-2",
) -> bool:
    """Check if a resource exists in AWS.

    Args:
        resource_type: Terraform resource type (e.g., 'aws_lambda_function')
        resource_name: The AWS resource name/identifier
        region: AWS region to check in

    Returns:
        True if the resource exists, False otherwise.

    Raises:
        ValueError: If the resource type is not supported.
    """
    if resource_type not in RESOURCE_CHECKERS:
        raise ValueError(
            f"Unsupported resource type: {resource_type}. "
            f"Supported types: {', '.join(RESOURCE_CHECKERS.keys())}"
        )

    client_name = RESOURCE_TO_CLIENT[resource_type]
    client = cast(Any, boto3).client(client_name, region_name=region)
    checker = RESOURCE_CHECKERS[resource_type]

    return checker(client, resource_name)


def get_planned_creates(
    terraform_dir: Path,
    timeout: int = 120,
) -> List[Dict[str, Any]]:
    """Run terraform plan and extract resources marked for creation.

    Args:
        terraform_dir: Path to directory containing Terraform files
        timeout: Timeout in seconds for terraform plan command

    Returns:
        List of dicts with keys: type, name, address, values
        where 'name' is the AWS resource name (not Terraform resource name)
    """
    result = subprocess.run(
        ["terraform", "plan", "-json", "-input=false"],
        capture_output=True,
        text=True,
        cwd=terraform_dir,
        timeout=timeout,
        check=False,
    )

    creates = []
    for line in result.stdout.splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") != "planned_change":
            continue

        change = entry.get("change", {})
        if change.get("action") != "create":
            continue

        resource = change.get("resource", {})
        resource_type = resource.get("resource_type", "")

        if resource_type not in RESOURCE_CHECKERS:
            continue

        # Extract the AWS resource name from planned values
        after_values = change.get("change", {}).get("after", {})

        # Different resource types use different name attributes
        name_field = _get_name_field(resource_type)
        resource_name = after_values.get(name_field, "")

        if resource_name:
            creates.append({
                "type": resource_type,
                "name": resource_name,
                "address": resource.get("addr", ""),
                "values": after_values,
            })

    return creates


def _get_name_field(resource_type: str) -> str:
    """Get the attribute name that contains the AWS resource name."""
    name_fields = {
        "aws_lambda_function": "function_name",
        "aws_iam_role": "name",
        "aws_cloudwatch_log_group": "name",
        "aws_dynamodb_table": "name",
        "aws_s3_bucket": "bucket",
        "aws_sqs_queue": "name",
        "aws_sns_topic": "arn",
        "aws_ssm_parameter": "name",
        "aws_secretsmanager_secret": "name",
        "aws_cloudwatch_event_rule": "name",
        "aws_api_gateway_rest_api": "id",
    }
    return name_fields.get(resource_type, "name")


def get_terraform_state_resources(terraform_dir: Path) -> List[str]:
    """Get list of resource addresses currently in Terraform state.

    Args:
        terraform_dir: Path to directory containing Terraform files

    Returns:
        List of resource addresses (e.g., 'aws_lambda_function.my_func')
    """
    result = subprocess.run(
        ["terraform", "state", "list"],
        capture_output=True,
        text=True,
        cwd=terraform_dir,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_resource_in_state(terraform_dir: Path, tf_address: str) -> bool:
    """Check if a resource is in Terraform state.

    Args:
        terraform_dir: Path to directory containing Terraform files
        tf_address: Terraform resource address (e.g., 'aws_lambda_function.my_func')

    Returns:
        True if the resource is in state, False otherwise.
    """
    state_resources = get_terraform_state_resources(terraform_dir)
    return tf_address in state_resources


def find_orphaned_resources(
    terraform_dir: Path,
    region: str = "us-east-2",
) -> List[Dict[str, str]]:
    """Find resources that exist in AWS but not in Terraform state.

    This detects resources that Terraform plans to create but already exist
    in AWS - indicating they were created outside of Terraform or the state
    was lost.

    Args:
        terraform_dir: Path to directory containing Terraform files
        region: AWS region to check in

    Returns:
        List of dicts with keys: type, name, address, import_command
    """
    planned = get_planned_creates(terraform_dir)
    orphaned = []

    for resource in planned:
        if check_resource_exists(resource["type"], resource["name"], region):
            orphaned.append({
                "type": resource["type"],
                "name": resource["name"],
                "address": resource["address"],
                "import_command": f"terraform import {resource['address']} {resource['name']}",
            })

    return orphaned
