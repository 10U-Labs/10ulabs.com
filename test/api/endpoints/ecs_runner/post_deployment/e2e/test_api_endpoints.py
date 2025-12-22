"""End-to-end tests for ECS runner API endpoints.

These tests verify the API endpoints by making real HTTP requests.
"""
import json

import boto3
import requests

from ..conftest import (
    make_authenticated_get,
    make_authenticated_post,
)


class TestECSRunnerStatusEndpoint:
    """Test ECS runner status endpoint."""

    def test_status_requires_auth(self, api_url):
        """Test that ECS runner status endpoint requires authentication."""
        response = requests.get(f"{api_url}/v1/ecs-runner", timeout=10)
        assert response.status_code == 403

    def test_status_accepts_valid_api_key(self, api_url, api_key):
        """Test that ECS runner status endpoint accepts valid API key."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert response.status_code == 200

    def test_status_returns_json(self, api_url, api_key):
        """Test that ECS runner status endpoint returns JSON content type."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert response.headers["Content-Type"] == "application/json"

    def test_status_has_success_field(self, api_url, api_key):
        """Test that ECS runner status response contains success field."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert "success" in response.json()

    def test_status_has_running_tasks_field(self, api_url, api_key):
        """Test that ECS runner status response contains running_tasks field."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert "running_tasks" in response.json()

    def test_status_has_tasks_field(self, api_url, api_key):
        """Test that ECS runner status response contains tasks field."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert "tasks" in response.json()

    def test_status_has_cluster_field(self, api_url, api_key):
        """Test that ECS runner status response contains cluster field."""
        response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
        assert "cluster" in response.json()


class TestECSRunnerPostValidation:
    """Test ECS runner POST endpoint validation."""

    def test_post_missing_job_id_returns_400(self, api_url, api_key):
        """Test that POST without job_id returns 400."""
        payload = {
            "job_labels": ["ephemeral-ecs-fargate"],
            "github_repo": "any/repo"
        }
        response = make_authenticated_post(
            f"{api_url}/v1/ecs-runner", api_key, json=payload
        )
        assert response.status_code == 400

    def test_post_missing_github_repo_returns_400(self, api_url, api_key):
        """Test that POST without github_repo returns 400."""
        payload = {
            "job_id": 666666,
            "job_labels": ["ephemeral-ecs-fargate"]
        }
        response = make_authenticated_post(
            f"{api_url}/v1/ecs-runner", api_key, json=payload
        )
        assert response.status_code == 400


def _invoke_lambda_get_status(config):
    """Invoke Lambda with GET request and return parsed payload."""
    function_name = config["lambda_function_name"]
    region = config["aws_region"]

    event = {
        "httpMethod": "GET",
        "path": "/v1/ecs-runner",
        "headers": {"x-test-mode": "true"}
    }

    lambda_client = boto3.client("lambda", region_name=region)
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event)
    )

    return json.loads(response["Payload"].read())


class TestLambdaImportPath:
    """Test Lambda import paths are correct."""

    def test_lambda_processes_events_without_import_error(self, config):
        """Verify ECS runner handler can process events with runner labels.

        This test invokes the Lambda with a GET request to check status.
        If runner_labels.py is missing from the package, the Lambda will
        fail with a ModuleNotFoundError on import.
        """
        payload = _invoke_lambda_get_status(config)

        # If runner_labels import failed, we'd get a 500 with ModuleNotFoundError
        error_msg = payload.get("errorMessage", "")
        assert "ModuleNotFoundError" not in error_msg, (
            f"Lambda import failed: {error_msg}"
        )

    def test_lambda_returns_status_code(self, config):
        """Verify ECS runner handler returns a status code."""
        payload = _invoke_lambda_get_status(config)
        status_code = payload.get("statusCode")
        assert status_code is not None, "Lambda response missing statusCode"

    def test_lambda_status_code_is_integer(self, config):
        """Verify ECS runner handler returns an integer status code."""
        payload = _invoke_lambda_get_status(config)
        status_code = payload.get("statusCode")
        assert isinstance(status_code, int), "statusCode should be an integer"
