"""Pytest fixtures for runners E2E tests.

These tests verify the runners router Lambda can process SQS messages
and route them to the appropriate EC2 or ECS runner endpoints.
"""
import json

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
)

__all__ = [
    "runners_initialized",
    "lambda_function_name",
    "sqs_queue_url",
    "sqs_dlq_name",
    "lambda_client",
    "sqs_client",
]


@pytest.fixture(scope="session")
def shared_config():
    """Get shared config."""
    return get_shared_config()


@pytest.fixture(scope="session")
def api_url(shared_config):
    """Get the API URL."""
    api_fqdn = shared_config.get("api_fqdn", "")
    if not api_fqdn:
        pytest.skip("api_fqdn not configured")
    return f"https://{api_fqdn}"


@pytest.fixture(scope="session")
def ssm_client():
    """Create an SSM client."""
    import boto3
    return boto3.client("ssm", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def api_key(ssm_client):
    """Get the API key from SSM."""
    try:
        response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
        return response['Parameter']['Value']
    except ssm_client.exceptions.ParameterNotFound:
        pytest.skip("API key not found in SSM")
        return None


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
def runners_endpoint(api_url):
    """Get the runners endpoint URL."""
    return f"{api_url}/v1/runners"


def make_authenticated_post(url: str, api_key: str, timeout: int = 30, **kwargs):
    """Make an authenticated POST request with the API key header."""
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.post(url, headers=headers, timeout=timeout, **kwargs)
