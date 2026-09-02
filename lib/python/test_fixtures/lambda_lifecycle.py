import re
from pathlib import Path
from typing import Optional


def _extract_block_content(content: str, start_pos: int) -> str:
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos : start_pos + i + 1]
    return content[start_pos:]


def _check_lambda_lifecycle_rules(lambda_tf_path: Path) -> None:
    with open(lambda_tf_path, encoding="utf-8") as f:
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
                f"Lambda function '{resource_name}' has environment variables but "
                "is missing a lifecycle rule with replace_triggered_by. "
                "When IAM roles are recreated, KMS grants become stale because "
                "they reference the old role ID. Add:\n\n"
                "  lifecycle {\n"
                "    replace_triggered_by = [aws_iam_role.<role_name>.id]\n"
                "  }"
            )


def create_lambda_lifecycle_tests(
    endpoint_src: Path, tf_files: Optional[list] = None
) -> type:
    if tf_files is None:
        tf_files = ["lambda.tf"]

    tf_paths = [endpoint_src / tf_file for tf_file in tf_files]

    class TestLambdaLifecycle:
        def test_lambda_with_env_vars_has_lifecycle_rule(self) -> None:
            for tf_path in tf_paths:
                if tf_path.exists():
                    _check_lambda_lifecycle_rules(tf_path)

        def test_terraform_files_configured(self) -> None:
            assert len(tf_paths) > 0, "No terraform files configured for testing"

    return TestLambdaLifecycle
