"""AWS client singletons for Lambda handlers."""

import json
from typing import Any

import boto3

cache: dict[str, Any] = {
    "dynamodb_client": None,
    "ec2_client": None,
    "ecs_client": None,
    "s3_client": None,
    "sns_client": None,
    "sqs_client": None,
    "ssm_client": None,
}


def get_dynamodb_client() -> Any:
    """Get or create DynamoDB client (singleton)."""
    if cache["dynamodb_client"] is None:
        cache["dynamodb_client"] = boto3.client("dynamodb")
    return cache["dynamodb_client"]


def get_ec2_client() -> Any:
    """Get or create EC2 client (singleton)."""
    if cache["ec2_client"] is None:
        cache["ec2_client"] = boto3.client("ec2")
    return cache["ec2_client"]


def get_ecs_client() -> Any:
    """Get or create ECS client (singleton)."""
    if cache["ecs_client"] is None:
        cache["ecs_client"] = boto3.client("ecs")
    return cache["ecs_client"]


def get_s3_client() -> Any:
    """Get or create S3 client (singleton)."""
    if cache["s3_client"] is None:
        cache["s3_client"] = boto3.client("s3")
    return cache["s3_client"]


def get_sns_client() -> Any:
    """Get or create SNS client (singleton)."""
    if cache["sns_client"] is None:
        cache["sns_client"] = boto3.client("sns")
    return cache["sns_client"]


def get_sqs_client() -> Any:
    """Get or create SQS client (singleton)."""
    if cache["sqs_client"] is None:
        cache["sqs_client"] = boto3.client("sqs")
    return cache["sqs_client"]


def get_ssm_client() -> Any:
    """Get or create SSM client (singleton)."""
    if cache["ssm_client"] is None:
        cache["ssm_client"] = boto3.client("ssm")
    return cache["ssm_client"]


def put_json_to_s3(bucket: str, key: str, data: dict) -> None:
    """Write a JSON object to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        data: Dictionary to serialize as JSON
    """
    get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )
