"""Pytest fixtures for runners E2E tests.

These tests verify the runners router Lambda can process SQS messages
and route them to the appropriate EC2 or ECS runner endpoints.
"""
import json

import boto3
import pytest
import requests

from terraform_config import TEST_AWS_REGION, get_shared_config
# Import shared fixtures from integration conftest for re-export
from ..integration.conftest import (
    runners_initialized,
    lambda_function_name,
    sqs_queue_url,
    sqs_dlq_name,
    lambda_client,
    sqs_client,
    sqs_redrive_policy,
)

__all__ = [
    "runners_initialized",
    "lambda_function_name",
    "sqs_queue_url",
    "sqs_dlq_name",
    "lambda_client",
    "sqs_client",
    "sqs_redrive_policy",
]


@pytest.fixture(scope="session")
def shared_config():
    """Get shared config."""
    return get_shared_config()


@pytest.fixture(scope="session")
def api_url(request):
    """Get the API URL."""
    config = request.getfixturevalue("shared_config")
    api_fqdn = config.get("api_fqdn", "")
    assert api_fqdn, (
        "api_fqdn not found in shared config. "
        "Check that domain_name is set in lib/terraform/common/outputs.tf"
    )
    return f"https://{api_fqdn}"


@pytest.fixture(scope="session")
def ssm_client():
    """Create an SSM client."""
    return boto3.client("ssm", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def api_key(request):
    """Get the API key from SSM."""
    client = request.getfixturevalue("ssm_client")
    response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return response['Parameter']['Value']


def create_sqs_event(message_body: dict, message_id: str = "test-msg-id") -> dict:
    """Create an SQS event for Lambda invocation testing."""
    return {
        "Records": [{
            "eventSource": "aws:sqs",
            "messageId": message_id,
            "body": json.dumps(message_body)
        }]
    }


def create_runner_request(
    runner_type: str,
    job_id: int = 12345,
    github_repo: str = "test/repo",
    run_id: int = 99999
) -> dict:
    """Create a runner request message body.

    Args:
        runner_type: 'ec2' or 'ecs'
        job_id: The GitHub job ID
        github_repo: The GitHub repository
        run_id: The GitHub run ID

    Returns:
        Message body dict for SQS event
    """
    if runner_type == "ec2":
        labels = ["ec2", "general-purpose", "arm", "spot", f"runner-{job_id}"]
    else:
        labels = ["ecs", "fargate", "arm", "spot", f"runner-{job_id}"]

    return {
        "job_id": job_id,
        "job_labels": labels,
        "github_repo": github_repo,
        "run_id": run_id
    }


@pytest.fixture(scope="session")
def runners_endpoint(request):
    """Get the runners endpoint URL."""
    url = request.getfixturevalue("api_url")
    return f"{url}/v1/runners"


def make_authenticated_post(url: str, key: str, timeout: int = 30, **kwargs):
    """Make an authenticated POST request with the API key header."""
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = key
    return requests.post(url, headers=headers, timeout=timeout, **kwargs)


def invoke_lambda(client, function_name: str, event: dict) -> dict:
    """Invoke Lambda and return the raw response.

    Args:
        client: boto3 Lambda client
        function_name: Name of the Lambda function
        event: Event payload to send

    Returns:
        Raw Lambda invoke response
    """
    return client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event)
    )


def parse_lambda_response(response: dict) -> tuple:
    """Parse Lambda response into payload, body, and results.

    Args:
        response: Raw Lambda invoke response

    Returns:
        Tuple of (payload_dict, body_dict, results_list)
    """
    payload = json.loads(response["Payload"].read())
    body = json.loads(payload.get("body", "{}"))
    results = body.get("results", [])
    return payload, body, results


def invoke_and_parse(client, function_name: str, event: dict) -> tuple:
    """Invoke Lambda and parse the response.

    Args:
        client: boto3 Lambda client
        function_name: Name of the Lambda function
        event: Event payload to send

    Returns:
        Tuple of (response, payload, body, results)
    """
    response = invoke_lambda(client, function_name, event)
    payload, body, results = parse_lambda_response(response)
    return response, payload, body, results
