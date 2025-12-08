"""Integration tests for ECS runner Lambda package contents.

These tests verify that deployed Lambda packages contain required shared modules.
"""
import json

from test.api.endpoints.conftest import assert_lambda_package_includes_file

import boto3


def test_ecs_runner_handler_package_includes_runner_labels(config):
    """Verify deployed ECS runner handler Lambda includes runner_labels.py.

    This is a regression test that validates the deployed Lambda package
    actually contains the runner_labels module. The Lambda will fail at
    runtime with a ModuleNotFoundError if this file is missing.
    """
    function_name = "TenULabsEcsRunnerHandler"
    region = config["aws_region"]
    assert_lambda_package_includes_file(function_name, "runner_labels.py", region)


def test_ecs_runner_handler_processes_labels_without_import_error(config):
    """Verify ECS runner handler can process events with runner labels.

    This test invokes the Lambda with a GET request to check status.
    If runner_labels.py is missing from the package, the Lambda will
    fail with a ModuleNotFoundError on import.
    """
    function_name = "TenULabsEcsRunnerHandler"
    region = config["aws_region"]

    # GET request to status endpoint - exercises the Lambda import path
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

    # Read response payload
    payload = json.loads(response["Payload"].read())

    # If runner_labels import failed, we'd get a 500 with ModuleNotFoundError
    assert response["StatusCode"] == 200
    error_msg = payload.get("errorMessage", "")
    assert "errorMessage" not in payload or "ModuleNotFoundError" not in error_msg
