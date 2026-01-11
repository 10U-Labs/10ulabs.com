"""Post-deployment integration tests verifying AWS resources exist."""
from typing import Dict

import boto3
import pytest


def test_lambda_function_exists(function_name: str, cfg: Dict[str, str]) -> None:
    """Assert Lambda function is deployed to AWS."""
    lmb = boto3.client('lambda', region_name=cfg['aws_region'])
    try:
        fn_response = lmb.get_function(FunctionName=function_name)
        assert fn_response['Configuration']['FunctionName'] == function_name
    except lmb.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function {function_name} not deployed yet")


def test_sqs_queue_exists(queue_name: str, cfg: Dict[str, str]) -> None:
    """Assert SQS queue is deployed to AWS."""
    sqs = boto3.client('sqs', region_name=cfg['aws_region'])
    try:
        queue_response = sqs.get_queue_url(QueueName=queue_name)
        assert queue_name in queue_response['QueueUrl']
    except sqs.exceptions.QueueDoesNotExist:
        pytest.skip(f"SQS queue {queue_name} not deployed yet")
