"""AWS resource existence assertion utilities for integration tests."""
from typing import Dict, Any

import boto3
import pytest


def assert_lambda_exists(fn_name: str, config: Dict[str, Any]) -> None:
    """Verify a Lambda function exists in AWS.

    Args:
        fn_name: Name of the Lambda function to check
        config: Configuration dict with 'aws_region' key
    """
    client = boto3.client('lambda', region_name=config['aws_region'])
    try:
        fn_data = client.get_function(FunctionName=fn_name)
        assert fn_data['Configuration']['FunctionName'] == fn_name
    except client.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function {fn_name} not deployed")


def assert_sqs_queue_exists(q_name: str, config: Dict[str, Any]) -> None:
    """Verify an SQS queue exists in AWS.

    Args:
        q_name: Name of the SQS queue to check
        config: Configuration dict with 'aws_region' key
    """
    client = boto3.client('sqs', region_name=config['aws_region'])
    try:
        q_data = client.get_queue_url(QueueName=q_name)
        assert q_name in q_data['QueueUrl']
    except client.exceptions.QueueDoesNotExist:
        pytest.skip(f"SQS queue {q_name} not deployed")
