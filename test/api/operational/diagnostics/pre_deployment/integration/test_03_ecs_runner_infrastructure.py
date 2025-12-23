"""Tests to validate ECS runner infrastructure exists for echo endpoint.

Five-layer testing model:
- Layer 3: Existence - Do the ECS runner resources exist?

These tests verify that ecs_runner resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestECSRunnerOutputs:
    """Layer 3: Verify ecs_runner terraform outputs are accessible."""

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
    """Layer 3: Verify the ECS runner Lambda function exists in AWS."""

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
