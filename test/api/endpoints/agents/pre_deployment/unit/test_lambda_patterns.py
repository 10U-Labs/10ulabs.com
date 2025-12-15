"""Unit tests for Lambda patterns in agents endpoint."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def _extract_block_content(content: str, start_pos: int) -> str:
    """Extract content of a Terraform block by counting braces."""
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos : start_pos + i + 1]
    return content[start_pos:]


class TestLambdaLifecycleRules:
    """Tests for Lambda lifecycle rules to prevent stale KMS grants."""

    def test_lambda_with_env_vars_has_lifecycle_block(self):
        """Test that Lambda functions with environment variables have lifecycle block.

        Lambdas using KMS-encrypted environment variables need lifecycle rules
        to refresh KMS grants when the IAM role changes.
        """
        lambda_file = AGENTS_SRC / "lambda.tf"
        with open(lambda_file, encoding="utf-8") as f:
            content = f.read()

        lambda_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'
        for match in re.finditer(lambda_pattern, content):
            resource_name = match.group(1)
            block_start = match.end() - 1
            block_content = _extract_block_content(content, block_start)

            has_env_vars = re.search(r"environment\s*\{", block_content)
            if has_env_vars:
                has_lifecycle = "lifecycle" in block_content
                assert has_lifecycle, (
                    f"Lambda '{resource_name}' has environment variables but no "
                    "lifecycle block. Add lifecycle.replace_triggered_by to "
                    "refresh KMS grants when IAM role changes."
                )

    def test_lambda_with_env_vars_has_replace_triggered_by(self):
        """Test that Lambda functions with environment variables have replace_triggered_by."""
        lambda_file = AGENTS_SRC / "lambda.tf"
        with open(lambda_file, encoding="utf-8") as f:
            content = f.read()

        lambda_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'
        for match in re.finditer(lambda_pattern, content):
            resource_name = match.group(1)
            block_start = match.end() - 1
            block_content = _extract_block_content(content, block_start)

            has_env_vars = re.search(r"environment\s*\{", block_content)
            if has_env_vars:
                has_replace_triggered_by = "replace_triggered_by" in block_content
                assert has_replace_triggered_by, (
                    f"Lambda '{resource_name}' has lifecycle but no "
                    "replace_triggered_by. Add replace_triggered_by = "
                    "[aws_iam_role.*.arn] to refresh KMS grants."
                )


class TestFunctionURLPermissions:
    """Tests for Lambda Function URL permissions."""

    def test_function_url_has_public_access_permission(self):
        """Test that Function URL has explicit public access permission.

        Lambda Function URLs with auth_type = NONE still need an explicit
        aws_lambda_permission resource for InvokeFunctionUrl.
        """
        lambda_file = AGENTS_SRC / "lambda.tf"
        with open(lambda_file, encoding="utf-8") as f:
            content = f.read()

        # Check if function URL exists
        has_function_url = 'resource "aws_lambda_function_url"' in content
        if has_function_url:
            # Should have permission for InvokeFunctionUrl
            has_invoke_permission = "InvokeFunctionUrl" in content
            assert has_invoke_permission, (
                "Function URL exists but no InvokeFunctionUrl permission found. "
                "Add aws_lambda_permission with function_url_auth_type."
            )
