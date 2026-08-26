import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

import boto3
from botocore.exceptions import ClientError


ResourceChecker = Callable[[Any, str], bool]


def _check_lambda(client: Any, name: str) -> bool:
    try:
        client.get_function(FunctionName=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_iam_role(client: Any, name: str) -> bool:
    try:
        client.get_role(RoleName=name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def _check_log_group(client: Any, name: str) -> bool:
    response = client.describe_log_groups(logGroupNamePrefix=name, limit=1)
    for group in response.get("logGroups", []):
        if group.get("logGroupName") == name:
            return True
    return False


def _check_dynamodb_table(client: Any, name: str) -> bool:
    try:
        client.describe_table(TableName=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_s3_bucket(client: Any, name: str) -> bool:
    try:
        client.head_bucket(Bucket=name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def _check_sqs_queue(client: Any, name: str) -> bool:
    try:
        client.get_queue_url(QueueName=name)
        return True
    except client.exceptions.QueueDoesNotExist:
        return False


def _check_sns_topic(client: Any, arn: str) -> bool:
    try:
        client.get_topic_attributes(TopicArn=arn)
        return True
    except client.exceptions.NotFoundException:
        return False


def _check_ssm_parameter(client: Any, name: str) -> bool:
    try:
        client.get_parameter(Name=name)
        return True
    except client.exceptions.ParameterNotFound:
        return False


def _check_secretsmanager_secret(client: Any, name: str) -> bool:
    try:
        client.describe_secret(SecretId=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_eventbridge_rule(client: Any, name: str) -> bool:
    try:
        client.describe_rule(Name=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def _check_api_gateway_rest_api(client: Any, api_id: str) -> bool:
    try:
        client.get_rest_api(restApiId=api_id)
        return True
    except client.exceptions.NotFoundException:
        return False


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


def check_resource_exists(
    resource_type: str,
    resource_name: str,
    region: str = "us-east-2",
) -> bool:
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

        after_values = change.get("change", {}).get("after", {})

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
