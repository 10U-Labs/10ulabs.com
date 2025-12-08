"""Integration tests for runners Lambda package contents.

These tests verify that deployed Lambda packages contain required shared modules.
"""
import json

from test.api.endpoints.conftest import assert_lambda_package_includes_file

import boto3


def test_webhook_handler_package_includes_runner_labels(config):
    """Verify deployed webhook handler Lambda includes runner_labels.py.

    This is a regression test that validates the deployed Lambda package
    actually contains the runner_labels module. The Lambda will fail at
    runtime with a ModuleNotFoundError if this file is missing.
    """
    function_name = "TenULabsWebhookHandler"
    region = config["aws_region"]
    assert_lambda_package_includes_file(function_name, "runner_labels.py", region)


def test_webhook_handler_processes_runner_labels_without_import_error(config):
    """Verify webhook handler can process events with runner labels.

    This test invokes the Lambda with a workflow_job event containing
    runner labels. If runner_labels.py is missing from the package,
    the Lambda will fail with a ModuleNotFoundError.
    """
    function_name = "TenULabsWebhookHandler"
    region = config["aws_region"]

    # Event with runner labels that exercises runner_labels.parse_labels()
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
                "labels": ["ecs", "fargate", "spot", "runner-12345"],
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

    # Read response payload
    payload = json.loads(response["Payload"].read())

    # If runner_labels import failed, we'd get a 500 with ModuleNotFoundError
    # A successful import means the Lambda could at least parse the labels
    assert response["StatusCode"] == 200
    error_msg = payload.get("errorMessage", "")
    assert "errorMessage" not in payload or "ModuleNotFoundError" not in error_msg
