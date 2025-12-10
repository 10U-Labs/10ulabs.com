"""Layer 3: Verify image_for_ec2_runners terraform outputs exist.

ec2_runner depends on image_for_ec2_runners being deployed first.
"""


class TestImageForEC2RunnersOutputsExistence:
    """Layer 3: Verify image_for_ec2_runners terraform outputs are accessible."""

    def test_01_lambda_function_arn_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_function_arn output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_function_arn"), (
            "lambda_function_arn output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )

    def test_02_lambda_function_name_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_function_name output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )

    def test_03_lambda_invoke_arn_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_invoke_arn output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_invoke_arn"), (
            "lambda_invoke_arn output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )
