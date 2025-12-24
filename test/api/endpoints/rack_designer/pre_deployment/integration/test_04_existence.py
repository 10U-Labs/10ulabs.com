"""Layer 4: Existence tests for rack_designer endpoint pre-deployment.

Tests that prerequisite resources from OTHER workflows exist.
Not configuration, not capability - just existence.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources actually exist
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites:
    """Layer 4: Verify api_backend resources exist."""

    def test_api_backend_outputs_provides_gateway_id(self, api_backend_outputs):
        """Verify api_backend terraform outputs provide api_gateway_rest_api_id."""
        assert api_backend_outputs.get("api_gateway_rest_api_id"), (
            "api_gateway_rest_api_id output not found in api_backend. "
            "Run terraform apply in src/api/backend/"
        )

    def test_api_gateway_rest_api_exists(self, api_gateway_info):
        """Verify the API Gateway REST API exists."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        assert api_gateway_info["exists"], (
            f"API Gateway '{api_gateway_info['id']}' does not exist. "
            "Run terraform apply in src/api/backend/"
        )


class TestECSRunnerPrerequisites:
    """Layer 4: Verify ecs_runner resources exist."""

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

    def test_lambda_function_name_output_exists(self, ecs_runner_outputs):
        """Verify lambda_function_name output is available."""
        assert ecs_runner_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )

    def test_ecs_runner_lambda_exists(self, lambda_client, ecs_runner_outputs):
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

    def test_ecs_runner_lambda_is_active(self, lambda_client, ecs_runner_outputs):
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


class TestWWWSharedPrerequisites:
    """Layer 4: Verify www_shared resources exist."""

    def test_bucket_name_output_exists(self, www_shared_outputs):
        """Verify bucket_name output is available."""
        assert www_shared_outputs.get("bucket_name"), (
            "bucket_name output not found in www_shared. "
            "Run terraform apply in src/www/shared/"
        )

    def test_s3_bucket_exists(self, s3_client, www_shared_outputs):
        """Verify the S3 bucket for designs exists."""
        bucket_name = www_shared_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"S3 bucket '{bucket_name}' does not exist. "
                    "Run terraform apply in src/www/shared/"
                )
            raise
