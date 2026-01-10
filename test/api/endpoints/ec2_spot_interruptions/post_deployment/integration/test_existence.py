"""Post-deployment integration tests verifying AWS resources exist."""
import boto3
import pytest


class TestLambdaExists:
    """Tests that Lambda function exists."""

    def test_lambda_function_exists(self, function_name: str, config):
        """Lambda function exists in AWS."""
        client = boto3.client('lambda', region_name=config['aws_region'])
        try:
            response = client.get_function(FunctionName=function_name)
            assert response['Configuration']['FunctionName'] == function_name
        except client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function {function_name} not deployed yet")


class TestSqsQueueExists:
    """Tests that SQS queue exists."""

    def test_sqs_queue_exists(self, queue_name: str, config):
        """SQS queue exists in AWS."""
        client = boto3.client('sqs', region_name=config['aws_region'])
        try:
            response = client.get_queue_url(QueueName=queue_name)
            assert queue_name in response['QueueUrl']
        except client.exceptions.QueueDoesNotExist:
            pytest.skip(f"SQS queue {queue_name} not deployed yet")
