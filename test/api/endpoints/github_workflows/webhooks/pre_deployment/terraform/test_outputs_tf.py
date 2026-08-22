"""Terraform unit tests for outputs.tf.

These tests verify Terraform outputs are correctly defined.
"""

import re

# Expected outputs
EXPECTED_OUTPUTS = [
    "lambda_function_arn",
    "lambda_function_name",
    "github_token_secret_name",
    "webhook_parameter_name",
    "webhook_parameter_arn",
    "api_endpoint",
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

    def test_outputs_have_value_attribute(self, outputs_tf_content):
        """Verify outputs have value attribute defined."""
        output_count = len(re.findall(r'output\s+"', outputs_tf_content))
        value_count = len(re.findall(r'value\s*=', outputs_tf_content))
        assert value_count >= output_count, (
            f"Not all outputs have value: found {value_count} for {output_count} outputs"
        )


class TestOutputValues:
    """Test output value references."""

    def test_lambda_function_arn_references_runners_handler(self, outputs_tf_content):
        """Verify lambda_function_arn references runners_handler."""
        pattern = (
            r'output\s+"lambda_function_arn"[^}]*'
            r'value\s*=\s*aws_lambda_function\.runners_handler\.arn'
        )
        assert re.search(pattern, outputs_tf_content, re.DOTALL), (
            "lambda_function_arn should reference runners_handler.arn"
        )

    def test_lambda_function_name_references_runners_handler(self, outputs_tf_content):
        """Verify lambda_function_name references runners_handler."""
        pattern = (
            r'output\s+"lambda_function_name"[^}]*'
            r'value\s*=\s*aws_lambda_function\.runners_handler\.function_name'
        )
        assert re.search(pattern, outputs_tf_content, re.DOTALL), (
            "lambda_function_name should reference runners_handler.function_name"
        )


class TestOutputCount:
    """Test output counts."""

    def test_minimum_outputs_defined(self, outputs_tf_content):
        """Verify minimum number of outputs are defined."""
        output_count = len(re.findall(r'output\s+"', outputs_tf_content))
        assert output_count >= len(EXPECTED_OUTPUTS), (
            f"Expected at least {len(EXPECTED_OUTPUTS)} outputs, found {output_count}"
        )

    def test_no_empty_outputs(self, outputs_tf_content):
        """Verify no outputs are empty strings."""
        empty_pattern = r'value\s*=\s*""'
        empty_count = len(re.findall(empty_pattern, outputs_tf_content))
        assert empty_count == 0, "Outputs should not have empty string values"
