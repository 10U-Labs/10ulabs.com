"""Unit tests for Lambda configuration patterns.

These tests parse Terraform files to verify best practices are followed:
1. Lambda Function URLs have explicit public access permissions
2. Lambdas with environment variables have lifecycle rules to handle IAM role recreation

These are regression tests for:
- 403 Forbidden errors when Function URL permission is missing
- 502 KMS errors when IAM role is recreated and KMS grant becomes stale
"""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
TROUBLESHOOTER_SRC = (
    REPO_ROOT / "src" / "api" / "endpoints" / "agents" / "troubleshooter_of_workflows"
)
LAMBDA_TF_PATH = TROUBLESHOOTER_SRC / "lambda.tf"


def _read_lambda_tf() -> str:
    """Read the lambda.tf file contents."""
    with open(LAMBDA_TF_PATH, encoding="utf-8") as f:
        return f.read()


def _extract_block_content(content: str, start_pos: int) -> str:
    """Extract content of a Terraform block starting at the given brace position."""
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos : start_pos + i + 1]
    return content[start_pos:]


class TestFunctionURLPermission:
    """Verify Lambda Function URLs have explicit public access permissions.

    When using authorization_type = "NONE" for Lambda Function URLs, an explicit
    aws_lambda_permission resource is required to allow public access. Without
    this, the Function URL returns 403 Forbidden.

    This is a regression test for the 403 Forbidden bug where the Function URL
    was configured but not publicly accessible.
    """

    def test_lambda_tf_exists(self):
        """Verify lambda.tf file exists."""
        assert LAMBDA_TF_PATH.exists(), f"lambda.tf not found at {LAMBDA_TF_PATH}"

    def test_function_url_has_invoke_permission(self):
        """Verify aws_lambda_permission with InvokeFunctionUrl exists.

        When aws_lambda_function_url with authorization_type = "NONE" exists,
        there must be a corresponding aws_lambda_permission with
        action = "lambda:InvokeFunctionUrl" to allow public access.
        """
        content = _read_lambda_tf()

        # Check if there's a Function URL resource
        has_function_url = "aws_lambda_function_url" in content

        if not has_function_url:
            # No Function URL, no permission needed
            return

        # Verify permission resource exists
        has_invoke_function_url = "lambda:InvokeFunctionUrl" in content

        assert has_invoke_function_url, (
            "Missing aws_lambda_permission for Function URL. "
            "When using aws_lambda_function_url with authorization_type = 'NONE', "
            "you must add an aws_lambda_permission resource with "
            "action = 'lambda:InvokeFunctionUrl' to allow public access. "
            "Without this, the Function URL returns 403 Forbidden."
        )

    def test_function_url_permission_has_auth_type(self):
        """Verify aws_lambda_permission includes function_url_auth_type.

        The permission should include function_url_auth_type = "NONE" to match
        the Function URL's authorization_type setting.
        """
        content = _read_lambda_tf()

        # Check if there's a Function URL resource
        has_function_url = "aws_lambda_function_url" in content

        if not has_function_url:
            # No Function URL, no permission needed
            return

        has_function_url_auth_type = "function_url_auth_type" in content

        assert has_function_url_auth_type, (
            "aws_lambda_permission for Function URL should include "
            "function_url_auth_type = 'NONE' to match the Function URL's "
            "authorization_type setting."
        )


class TestLifecycleRuleForKMSGrant:
    """Verify Lambdas with environment variables have lifecycle rules.

    When a Lambda has environment variables, AWS encrypts them with a KMS key
    and creates a KMS grant referencing the Lambda's IAM role ID. If the role
    is recreated (e.g., due to name changes), the grant becomes stale because
    it still references the old role ID.

    The fix is to add a lifecycle rule that forces Lambda replacement when
    the IAM role changes, which triggers AWS to create a new KMS grant.

    This is a regression test for the KMSAccessDeniedException bug (502 errors).
    """

    def test_lambda_with_env_vars_has_lifecycle_rule(self):
        """Verify Lambdas with environment variables have replace_triggered_by.

        Any aws_lambda_function with an environment block should have:
        lifecycle {
            replace_triggered_by = [aws_iam_role.<role>.id]
        }
        """
        content = _read_lambda_tf()

        # Find all Lambda function resources
        lambda_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'
        for match in re.finditer(lambda_pattern, content):
            resource_name = match.group(1)
            block_start = match.end() - 1
            block_content = _extract_block_content(content, block_start)

            # Check if this Lambda has environment variables
            has_env_vars = re.search(r"environment\s*\{", block_content)

            if has_env_vars:
                # Must have lifecycle rule with replace_triggered_by
                has_lifecycle = "lifecycle" in block_content
                has_replace_triggered_by = "replace_triggered_by" in block_content

                assert has_lifecycle and has_replace_triggered_by, (
                    f"Lambda function '{resource_name}' has environment variables but "
                    "is missing a lifecycle rule with replace_triggered_by. "
                    "When IAM roles are recreated, KMS grants become stale because "
                    "they reference the old role ID. Add:\n\n"
                    "  lifecycle {\n"
                    "    replace_triggered_by = [aws_iam_role.<role_name>.id]\n"
                    "  }\n\n"
                    "This forces Lambda replacement when the role changes, "
                    "triggering AWS to create a new KMS grant."
                )

    def test_lifecycle_rule_references_iam_role(self):
        """Verify lifecycle rule references an IAM role.

        The replace_triggered_by should reference aws_iam_role.*.id to trigger
        replacement when the role is recreated.
        """
        content = _read_lambda_tf()

        # Find lifecycle blocks with replace_triggered_by
        lifecycle_pattern = r"lifecycle\s*\{[^}]*replace_triggered_by\s*=\s*\[([^\]]+)\]"
        for match in re.finditer(lifecycle_pattern, content, re.DOTALL):
            trigger_value = match.group(1)

            # Should reference an IAM role's id attribute
            assert "aws_iam_role" in trigger_value and ".id" in trigger_value, (
                f"replace_triggered_by should reference aws_iam_role.<name>.id, "
                f"found: {trigger_value.strip()}"
            )
