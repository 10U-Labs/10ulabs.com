"""Unit tests for Lambda lifecycle configuration.

Verifies Lambdas with environment variables have lifecycle rules to handle
IAM role recreation. This is a regression test for 502 KMS errors when
IAM roles are recreated and KMS grants become stale.
"""

import re

import pytest
from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_designer"
LAMBDA_TF_FILES = [
    ENDPOINT_SRC / "lambda.tf",
    ENDPOINT_SRC / "analytics.tf",
]


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


@pytest.mark.parametrize("tf_file", LAMBDA_TF_FILES, ids=lambda p: p.name)
def test_lambda_with_env_vars_has_lifecycle_rule(tf_file):
    """Verify Lambda with environment variables has replace_triggered_by."""
    if not tf_file.exists():
        pytest.skip(f"{tf_file.name} does not exist")

    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    lambda_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'
    for match in re.finditer(lambda_pattern, content):
        resource_name = match.group(1)
        block_start = match.end() - 1
        block_content = _extract_block_content(content, block_start)

        has_env_vars = re.search(r"environment\s*\{", block_content)
        if has_env_vars:
            has_lifecycle = "lifecycle" in block_content
            has_replace_triggered_by = "replace_triggered_by" in block_content

            assert has_lifecycle and has_replace_triggered_by, (
                f"Lambda function '{resource_name}' in {tf_file.name} has "
                "environment variables but is missing a lifecycle rule with "
                "replace_triggered_by. When IAM roles are recreated, KMS grants "
                "become stale because they reference the old role ID. Add:\n\n"
                "  lifecycle {\n"
                "    replace_triggered_by = [aws_iam_role.<role_name>.id]\n"
                "  }"
            )
