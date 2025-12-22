"""AWS client singletons for Lambda handlers."""

from typing import Any

import boto3

_cache: dict[str, Any] = {
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
    if _cache["dynamodb_client"] is None:
        _cache["dynamodb_client"] = boto3.client("dynamodb")
    return _cache["dynamodb_client"]


def get_ec2_client() -> Any:
    """Get or create EC2 client (singleton)."""
    if _cache["ec2_client"] is None:
        _cache["ec2_client"] = boto3.client("ec2")
    return _cache["ec2_client"]


def get_ecs_client() -> Any:
    """Get or create ECS client (singleton)."""
    if _cache["ecs_client"] is None:
        _cache["ecs_client"] = boto3.client("ecs")
    return _cache["ecs_client"]


def get_s3_client() -> Any:
    """Get or create S3 client (singleton)."""
    if _cache["s3_client"] is None:
        _cache["s3_client"] = boto3.client("s3")
    return _cache["s3_client"]


def get_sns_client() -> Any:
    """Get or create SNS client (singleton)."""
    if _cache["sns_client"] is None:
        _cache["sns_client"] = boto3.client("sns")
    return _cache["sns_client"]


def get_sqs_client() -> Any:
    """Get or create SQS client (singleton)."""
    if _cache["sqs_client"] is None:
        _cache["sqs_client"] = boto3.client("sqs")
    return _cache["sqs_client"]


def get_ssm_client() -> Any:
    """Get or create SSM client (singleton)."""
    if _cache["ssm_client"] is None:
        _cache["ssm_client"] = boto3.client("ssm")
    return _cache["ssm_client"]
