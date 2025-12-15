"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import re
from pathlib import Path

import pytest

from naming_conventions import validate_name

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
IMAGE_EC2_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
IAM_FILE = IMAGE_EC2_SRC / "iam.tf"
LAMBDA_FILE = IMAGE_EC2_SRC / "lambda.tf"


def get_resource_prefix() -> str:
    """Get the resource prefix from shared Terraform module."""
    shared_locals = REPO_ROOT / "lib" / "terraform" / "modules" / "shared" / "locals.tf"
    with open(shared_locals, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'resource_prefix\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "TenULabs"


def find_block_end(content: str, start_pos: int) -> int:
    """Find the end position of a brace-delimited block."""
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return start_pos + i + 1
    return start_pos


def extract_terraform_resources(tf_file: Path, resource_type: str, name_attr: str) -> list:
    """Extract resource names from a Terraform file."""
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    resources = []
    pattern = rf'resource\s+"{resource_type}"\s+"([^"]+)"\s*\{{'

    for match in re.finditer(pattern, content):
        resource_name = match.group(1)
        start_pos = match.end() - 1
        block_content = content[start_pos:find_block_end(content, start_pos)]
        name_match = re.search(rf'^\s*{name_attr}\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            resolved = name_match.group(1).replace("${local.resource_prefix}", prefix)
            resources.append((resource_name, resolved))

    return resources


def extract_iam_role_names(tf_file: Path) -> list:
    """Extract IAM role names from a Terraform file."""
    return extract_terraform_resources(tf_file, "aws_iam_role", "name")


def extract_lambda_function_names(tf_file: Path) -> list:
    """Extract Lambda function names from a Terraform file."""
    return extract_terraform_resources(tf_file, "aws_lambda_function", "function_name")


IAM_ROLES = extract_iam_role_names(IAM_FILE)
LAMBDA_FUNCTIONS = extract_lambda_function_names(LAMBDA_FILE)


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,role_name",
        IAM_ROLES if IAM_ROLES else [("NONE", "NONE")],
        ids=[f"iam_role_{r[0]}" for r in IAM_ROLES] if IAM_ROLES else ["no_roles_found"],
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if resource_name == "NONE":
            pytest.fail("No IAM roles found in iam.tf - check Terraform files")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        """Verify no IAM role names contain dashes."""
        violations = [(r, n) for r, n in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )


class TestLambdaFunctionNamingConventions:
    """Tests for Lambda function naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,function_name",
        LAMBDA_FUNCTIONS if LAMBDA_FUNCTIONS else [("NONE", "NONE")],
        ids=([f"lambda_{f[0]}" for f in LAMBDA_FUNCTIONS]
             if LAMBDA_FUNCTIONS else ["no_functions_found"]),
    )
    def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
        """Verify Lambda function name uses PascalCase (no dashes or underscores)."""
        if resource_name == "NONE":
            pytest.fail("No Lambda functions found in lambda.tf - check Terraform files")
        error = validate_name(function_name)
        assert error is None, (
            f"Lambda function '{resource_name}' has invalid name '{function_name}': {error}"
        )

    def test_no_lambda_function_names_contain_dashes(self):
        """Verify no Lambda function names contain dashes."""
        violations = [(r, n) for r, n in LAMBDA_FUNCTIONS if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} Lambda functions with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )
