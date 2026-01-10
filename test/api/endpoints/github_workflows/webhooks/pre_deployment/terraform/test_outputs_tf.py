"""Terraform unit tests for outputs.tf.

These tests verify Terraform outputs are correctly defined.
"""

import re

# Expected outputs
EXPECTED_OUTPUTS = [
    "lambda_function_arn",
    "lambda_function_name",
    "vpc_id",
    "public_subnets_ids",
    "security_group_id_for_runners",
    "github_token_secret_name",
    "webhook_parameter_name",
    "webhook_parameter_arn",
    "ecr_repository_arn",
    "ecr_repository_name",
    "ecr_repository_uri",
    "api_endpoint",
    "webhook_ingress_queue_url",
    "webhook_ingress_queue_arn",
    "webhook_ingress_queue_name",
]


class TestOutputsExist:
    """Test that all expected outputs are defined."""

    def test_all_expected_outputs_exist(self, outputs_tf_content):
        """Verify all expected outputs are defined."""
        for output_name in EXPECTED_OUTPUTS:
            pattern = rf'output\s+"{output_name}"'
            assert re.search(pattern, outputs_tf_content), (
                f"Output '{output_name}' not found in outputs.tf"
            )


class TestOutputValues:
    """Test output value references."""

    def test_lambda_function_arn_references_runners_handler(self, outputs_tf_content):
        """Verify lambda_function_arn references runners_handler."""
        pattern = r'output\s+"lambda_function_arn"[^}]*value\s*=\s*aws_lambda_function\.runners_handler\.arn'
        assert re.search(pattern, outputs_tf_content, re.DOTALL), (
            "lambda_function_arn should reference runners_handler.arn"
        )

    def test_lambda_function_name_references_runners_handler(self, outputs_tf_content):
        """Verify lambda_function_name references runners_handler."""
        pattern = r'output\s+"lambda_function_name"[^}]*value\s*=\s*aws_lambda_function\.runners_handler\.function_name'
        assert re.search(pattern, outputs_tf_content, re.DOTALL), (
            "lambda_function_name should reference runners_handler.function_name"
        )

    def test_webhook_ingress_queue_url_references_sqs(self, outputs_tf_content):
        """Verify webhook_ingress_queue_url references SQS queue."""
        pattern = r'output\s+"webhook_ingress_queue_url"[^}]*value\s*=\s*aws_sqs_queue\.webhook_ingress\.url'
        assert re.search(pattern, outputs_tf_content, re.DOTALL), (
            "webhook_ingress_queue_url should reference webhook_ingress.url"
        )


class TestOutputDescriptions:
    """Test that outputs have descriptions where appropriate."""

    def test_webhook_outputs_have_descriptions(self, outputs_tf_content):
        """Verify webhook-related outputs have descriptions."""
        webhook_outputs = [
            "webhook_ingress_queue_url",
            "webhook_ingress_queue_arn",
            "webhook_ingress_queue_name",
        ]
        for output_name in webhook_outputs:
            # Find the output block
            pattern = rf'output\s+"{output_name}"\s*\{{[^}}]*description\s*='
            assert re.search(pattern, outputs_tf_content, re.DOTALL), (
                f"Output '{output_name}' should have a description"
            )


class TestRemoteStateReferences:
    """Test outputs that reference remote state."""

    def test_vpc_id_references_remote_state(self, outputs_tf_content):
        """Verify vpc_id references remote state."""
        pattern = r'data\.terraform_remote_state\.\w+\.outputs\.vpc_id'
        assert re.search(pattern, outputs_tf_content), (
            "vpc_id should reference terraform_remote_state outputs"
        )

    def test_ecr_outputs_reference_remote_state(self, outputs_tf_content):
        """Verify ECR outputs reference remote state."""
        pattern = r'data\.terraform_remote_state\.api_common_docker_repository\.outputs'
        assert re.search(pattern, outputs_tf_content), (
            "ECR outputs should reference api_common_docker_repository remote state"
        )


class TestOutputCount:
    """Test output counts."""

    def test_minimum_outputs_defined(self, outputs_tf_content):
        """Verify minimum number of outputs are defined."""
        output_count = len(re.findall(r'output\s+"', outputs_tf_content))
        assert output_count >= len(EXPECTED_OUTPUTS), (
            f"Expected at least {len(EXPECTED_OUTPUTS)} outputs, found {output_count}"
        )
