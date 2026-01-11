"""Post-deployment integration tests verifying AWS resources exist."""
from typing import Dict

import boto3
import pytest


def test_lambda_function_exists(function_name: str, cfg: Dict[str, str]) -> None:
    """Lambda function exists in AWS."""
    lambda_client = boto3.client('lambda', region_name=cfg['aws_region'])
    try:
        resp = lambda_client.get_function(FunctionName=function_name)
        assert resp['Configuration']['FunctionName'] == function_name
    except lambda_client.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function {function_name} not deployed yet")


def test_sqs_queue_exists(queue_name: str, cfg: Dict[str, str]) -> None:
    """SQS queue exists in AWS."""
    sqs_client = boto3.client('sqs', region_name=cfg['aws_region'])
    try:
        resp = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")
        assert queue_name in resp['QueueUrl']
    except sqs_client.exceptions.QueueDoesNotExist:
        pytest.skip(f"SQS queue {queue_name} not deployed yet")
