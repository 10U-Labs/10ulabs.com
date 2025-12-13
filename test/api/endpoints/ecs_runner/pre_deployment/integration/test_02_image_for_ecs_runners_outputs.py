"""Tests to validate image_for_ecs_runners infrastructure exists.

Five-layer testing model:
- Layer 3: Existence - Do the terraform outputs exist?

These tests verify that image_for_ecs_runners resources this endpoint depends on exist.
"""


class TestImageForECSRunnersOutputs:
    """Layer 3: Verify image_for_ecs_runners terraform outputs are accessible."""

    def test_lambda_function_arn_output_exists(self, image_for_ecs_runners_outputs):
        """Verify lambda_function_arn output is available."""
        assert image_for_ecs_runners_outputs.get("lambda_function_arn"), (
            "lambda_function_arn output not found in image_for_ecs_runners. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/endpoint/"
        )

    def test_lambda_function_name_output_exists(self, image_for_ecs_runners_outputs):
        """Verify lambda_function_name output is available."""
        assert image_for_ecs_runners_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found in image_for_ecs_runners. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/endpoint/"
        )

    def test_lambda_invoke_arn_output_exists(self, image_for_ecs_runners_outputs):
        """Verify lambda_invoke_arn output is available."""
        assert image_for_ecs_runners_outputs.get("lambda_invoke_arn"), (
            "lambda_invoke_arn output not found in image_for_ecs_runners. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/endpoint/"
        )
