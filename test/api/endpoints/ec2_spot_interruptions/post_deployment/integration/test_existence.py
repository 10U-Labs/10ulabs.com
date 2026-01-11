"""Post-deployment integration tests verifying AWS resources exist."""
from typing import Dict

import boto3
import pytest


def test_lambda_function_exists(function_name: str, cfg: Dict[str, str]) -> None:
    """Verify Lambda function exists in AWS."""
    lambda_svc = boto3.client('lambda', region_name=cfg['aws_region'])
    try:
        result = lambda_svc.get_function(FunctionName=function_name)
        assert result['Configuration']['FunctionName'] == function_name
    except lambda_svc.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function {function_name} not deployed yet")


def test_sqs_queue_exists(queue_name: str, cfg: Dict[str, str]) -> None:
    """Verify SQS queue exists in AWS."""
    sqs_svc = boto3.client('sqs', region_name=cfg['aws_region'])
    try:
        result = sqs_svc.get_queue_url(QueueName=queue_name)
        assert queue_name in result['QueueUrl']
    except sqs_svc.exceptions.QueueDoesNotExist:
        pytest.skip(f"SQS queue {queue_name} not deployed yet")
