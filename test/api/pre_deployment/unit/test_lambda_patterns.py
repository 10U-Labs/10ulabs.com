"""Global unit tests for Lambda configuration patterns across all API endpoints.

These tests scan ALL Lambda Terraform files in src/api/endpoints/ to verify
best practices are followed:

1. Lambda Function URLs have explicit public access permissions
2. Lambdas with environment variables have lifecycle rules to handle IAM role recreation

These are regression tests for:
- 403 Forbidden errors when Function URL permission is missing
- 502 KMS errors when IAM role is recreated and KMS grant becomes stale
"""

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SRC_API_ENDPOINTS = REPO_ROOT / "src" / "api" / "endpoints"


def _find_all_lambda_tf_files() -> list[Path]:
    """Find all lambda.tf files in src/api/endpoints/."""
    return list(SRC_API_ENDPOINTS.rglob("lambda.tf"))


def _find_all_analytics_tf_files() -> list[Path]:
    """Find all analytics.tf files that may contain Lambda resources."""
    return list(SRC_API_ENDPOINTS.rglob("analytics.tf"))


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


def _get_all_lambda_files() -> list[Path]:
    """Get all Terraform files that contain Lambda resources."""
    files = _find_all_lambda_tf_files() + _find_all_analytics_tf_files()
    return [f for f in files if f.exists()]


class TestFunctionURLPermissionGlobal:
    """Verify all Lambda Function URLs have explicit public access permissions.

    When using authorization_type = "NONE" for Lambda Function URLs, an explicit
    aws_lambda_permission resource is required to allow public access. Without
    this, the Function URL returns 403 Forbidden.
    """

    def _get_files_with_function_urls(self) -> list[tuple[Path, str]]:
        """Find all Terraform files that have Function URL resources."""
        files_with_urls = []
        for tf_file in _get_all_lambda_files():
            content = tf_file.read_text()
            if "aws_lambda_function_url" in content:
                files_with_urls.append((tf_file, content))
        return files_with_urls

    def test_function_url_has_invoke_permission(self):
        """Verify aws_lambda_permission with InvokeFunctionUrl exists for each Function URL."""
        files_with_urls = self._get_files_with_function_urls()

        if not files_with_urls:
            pytest.skip("No Lambda Function URLs found in codebase")

        missing_permissions = []
        for tf_file, content in files_with_urls:
            if "lambda:InvokeFunctionUrl" not in content:
                missing_permissions.append(str(tf_file.relative_to(REPO_ROOT)))

        assert not missing_permissions, (
            "The following files have aws_lambda_function_url but are missing "
            "aws_lambda_permission with action = 'lambda:InvokeFunctionUrl':\n\n"
            + "\n".join(f"  - {f}" for f in missing_permissions)
            + "\n\nWhen using aws_lambda_function_url with authorization_type = 'NONE', "
            "you must add an aws_lambda_permission resource with "
            "action = 'lambda:InvokeFunctionUrl' to allow public access. "
            "Without this, the Function URL returns 403 Forbidden."
        )

    def test_function_url_permission_has_auth_type(self):
        """Verify aws_lambda_permission includes function_url_auth_type."""
        files_with_urls = self._get_files_with_function_urls()

        if not files_with_urls:
            pytest.skip("No Lambda Function URLs found in codebase")

        missing_auth_type = []
        for tf_file, content in files_with_urls:
            # Only check files that have Function URL and the permission
            if "lambda:InvokeFunctionUrl" in content:
                if "function_url_auth_type" not in content:
                    missing_auth_type.append(str(tf_file.relative_to(REPO_ROOT)))

        assert not missing_auth_type, (
            "The following files have InvokeFunctionUrl permission but are missing "
            "function_url_auth_type:\n\n"
            + "\n".join(f"  - {f}" for f in missing_auth_type)
            + "\n\naws_lambda_permission for Function URL should include "
            "function_url_auth_type = 'NONE' to match the Function URL's "
            "authorization_type setting."
        )


class TestLifecycleRuleForKMSGrantGlobal:
    """Verify all Lambdas with environment variables have lifecycle rules.

    When a Lambda has environment variables, AWS encrypts them with a KMS key
    and creates a KMS grant referencing the Lambda's IAM role ID. If the role
    is recreated (e.g., due to name changes), the grant becomes stale because
    it still references the old role ID.

    The fix is to add a lifecycle rule that forces Lambda replacement when
    the IAM role changes, which triggers AWS to create a new KMS grant.
    """

    def _find_lambdas_with_env_vars(self) -> list[tuple[Path, str, str]]:
        """Find all Lambda resources that have environment variables.

        Returns list of (file_path, resource_name, block_content) tuples.
        """
        lambdas_with_env = []
        lambda_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'

        for tf_file in _get_all_lambda_files():
            content = tf_file.read_text()

            for match in re.finditer(lambda_pattern, content):
                resource_name = match.group(1)
                block_start = match.end() - 1
                block_content = _extract_block_content(content, block_start)

                if re.search(r"environment\s*\{", block_content):
                    lambdas_with_env.append((tf_file, resource_name, block_content))

        return lambdas_with_env

    def test_lambda_with_env_vars_has_lifecycle_rule(self):
        """Verify Lambdas with environment variables have replace_triggered_by."""
        lambdas_with_env = self._find_lambdas_with_env_vars()

        if not lambdas_with_env:
            pytest.skip("No Lambda functions with environment variables found")

        missing_lifecycle = []
        for tf_file, resource_name, block_content in lambdas_with_env:
            has_lifecycle = "lifecycle" in block_content
            has_replace_triggered_by = "replace_triggered_by" in block_content

            if not (has_lifecycle and has_replace_triggered_by):
                relative_path = tf_file.relative_to(REPO_ROOT)
                missing_lifecycle.append(f"{relative_path} (resource: {resource_name})")

        assert not missing_lifecycle, (
            "The following Lambda functions have environment variables but are "
            "missing lifecycle { replace_triggered_by = [...] }:\n\n"
            + "\n".join(f"  - {f}" for f in missing_lifecycle)
            + "\n\nWhen IAM roles are recreated, KMS grants become stale because "
            "they reference the old role ID. Add:\n\n"
            "  lifecycle {\n"
            "    replace_triggered_by = [aws_iam_role.<role_name>.id]\n"
            "  }\n\n"
            "This forces Lambda replacement when the role changes, "
            "triggering AWS to create a new KMS grant."
        )

    def test_lifecycle_rule_references_iam_role(self):
        """Verify lifecycle rule references an IAM role."""
        lambdas_with_env = self._find_lambdas_with_env_vars()

        if not lambdas_with_env:
            pytest.skip("No Lambda functions with environment variables found")

        invalid_triggers = []
        lifecycle_pattern = (
            r"lifecycle\s*\{[^}]*replace_triggered_by\s*=\s*\[([^\]]+)\]"
        )

        for tf_file, resource_name, block_content in lambdas_with_env:
            for match in re.finditer(lifecycle_pattern, block_content, re.DOTALL):
                trigger_value = match.group(1)

                if "aws_iam_role" not in trigger_value or ".id" not in trigger_value:
                    relative_path = tf_file.relative_to(REPO_ROOT)
                    invalid_triggers.append(
                        f"{relative_path} (resource: {resource_name}): "
                        f"trigger = {trigger_value.strip()}"
                    )

        assert not invalid_triggers, (
            "The following Lambda lifecycle rules don't reference aws_iam_role.<name>.id:\n\n"
            + "\n".join(f"  - {t}" for t in invalid_triggers)
            + "\n\nreplace_triggered_by should reference aws_iam_role.<name>.id to "
            "trigger Lambda replacement when the IAM role is recreated."
        )
