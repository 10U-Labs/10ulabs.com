"""Pytest fixtures for runners integration tests."""
import json

from test.api.conftest import skip_if_endpoint_not_deployed

import boto3
import pytest
import requests

from runner_labels import DEFAULT_ECS_ARCH, DEFAULT_ECS_COMPUTE, DEFAULT_RUNNER_ID

# Re-export for local imports
__all__ = ['skip_if_endpoint_not_deployed']


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="sqs_client", scope="session")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="session")
def ecs_client_fixture(aws_region):
    """Provide an ECS client for the configured region."""
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API URL from config."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve the API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture(ssm_client, config):
    """Retrieve the GitHub PAT from SSM Parameter Store."""
    param_name = config.get('ssm_parameter_name_for_github_pat')
    param_response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_repo", scope="module")
def github_repo_fixture(config):
    """Provide the GitHub repository from config."""
    return config["github_repo"]


def make_health_check_request(api_url, api_key):
    """Make an HTTP request to the health check endpoint."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    """Assert that the response contains circuit breaker state."""
    data = response.json()
    assert data["circuit_breaker"] is not None


def create_test_dynamodb_item(client, table_name, item):
    """Create a test item in DynamoDB."""
    client.put_item(TableName=table_name, Item=item)


def cleanup_test_dynamodb_item(client, table_name, key):
    """Delete a test item from DynamoDB."""
    client.delete_item(TableName=table_name, Key=key)


@pytest.fixture(name="webhook_handler_response", scope="module")
def webhook_handler_response_fixture(config):
    """Invoke webhook handler Lambda with runner labels event."""
    function_name = "TenULabsWebhookHandler"
    region = config["aws_region"]

    event = {
        "httpMethod": "POST",
        "path": "/v1/runners",
        "headers": {
            "x-github-event": "workflow_job",
            "x-test-mode": "true"
        },
        "body": json.dumps({
            "action": "queued",
            "workflow_job": {
                "id": 999999,
                "run_id": 888888,
                "name": "test-job",
                "labels": [
                    "ecs",
                    DEFAULT_ECS_COMPUTE,
                    DEFAULT_ECS_ARCH,
                    "spot",
                    DEFAULT_RUNNER_ID,
                ],
                "status": "queued"
            },
            "repository": {"full_name": "test/repo"}
        })
    }

    lambda_client = boto3.client("lambda", region_name=region)
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event)
    )

    payload = json.loads(response["Payload"].read())
    return {"response": response, "payload": payload}
