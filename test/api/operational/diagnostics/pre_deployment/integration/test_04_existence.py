"""Layer 4: Existence tests for diagnostics endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify that resources from OTHER workflows that THIS workflow
depends on exist before deployment.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources exist
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites:
    """Layer 4: Verify api_backend prerequisites exist."""

    def test_api_gateway_rest_api_id_output_exists(self, api_backend_outputs):
        """Verify api_gateway_rest_api_id output is available from api_backend."""
        assert api_backend_outputs.get("api_gateway_rest_api_id"), (
            "api_gateway_rest_api_id output not found in api_backend. "
            "Run terraform apply in src/api/backend/"
        )

    def test_api_gateway_exists_in_aws(self, apigateway_client, api_backend_outputs):
        """Verify the API Gateway exists in AWS."""
        api_id = api_backend_outputs.get("api_gateway_rest_api_id")
        if not api_id:
            pytest.skip("api_gateway_rest_api_id output not available")
        try:
            response = apigateway_client.get_rest_api(restApiId=api_id)
            assert response["id"] == api_id, (
                f"API Gateway ID mismatch: expected {api_id}, got {response['id']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"API Gateway '{api_id}' does not exist. "
                    "Run terraform apply in src/api/backend/"
                )
            raise


class TestECSRunnerPrerequisites:
    """Layer 4: Verify ecs_runner prerequisites exist."""

    def test_cluster_arn_output_exists(self, ecs_runner_outputs):
        """Verify cluster_arn output is available."""
        assert ecs_runner_outputs.get("cluster_arn"), (
            "cluster_arn output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )

    def test_cluster_name_output_exists(self, ecs_runner_outputs):
        """Verify cluster_name output is available."""
        assert ecs_runner_outputs.get("cluster_name"), (
            "cluster_name output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )

    def test_task_definition_arn_output_exists(self, ecs_runner_outputs):
        """Verify task_definition_arn output is available."""
        assert ecs_runner_outputs.get("task_definition_arn"), (
            "task_definition_arn output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )

    def test_lambda_function_name_output_exists(self, ecs_runner_outputs):
        """Verify lambda_function_name output is available."""
        assert ecs_runner_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )


class TestECSRunnerLambdaExistence:
    """Layer 4: Verify the ECS runner Lambda function exists in AWS."""

    def test_lambda_function_exists(self, lambda_client, ecs_runner_outputs):
        """Verify the ECS runner Lambda function exists."""
        function_name = ecs_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        try:
            lambda_client.get_function(FunctionName=function_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{function_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/ecs_runner/"
                )
            raise

    def test_lambda_function_is_active(self, lambda_client, ecs_runner_outputs):
        """Verify the ECS runner Lambda function is active."""
        function_name = ecs_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            state = response["Configuration"]["State"]
            assert state == "Active", (
                f"Lambda function '{function_name}' is not active (state: {state}). "
                "Check Lambda function configuration."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise
