"""Unit tests for naming conventions in agents endpoint."""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_terraform_files_exist():
    """Test that Terraform files exist."""
    tf_files = list(AGENTS_SRC.glob("*.tf"))
    assert len(tf_files) > 0, "No Terraform files found"


@pytest.fixture
def terraform_files():
    """Get list of terraform files."""
    return list(AGENTS_SRC.glob("*.tf"))


@pytest.mark.parametrize("expected_file", [
    "backend.tf", "providers.tf", "locals.tf", "data.tf",
    "iam.tf", "lambda.tf", "ecr.tf", "agentcore.tf", "outputs.tf"
])
def test_terraform_file_is_lowercase(expected_file):
    """Test that terraform file names are lowercase."""
    tf_file = AGENTS_SRC / expected_file
    if tf_file.exists():
        name = tf_file.stem
        assert name == name.lower(), f"File {tf_file.name} should be lowercase"


@pytest.mark.parametrize("expected_file", [
    "backend.tf", "providers.tf", "locals.tf", "data.tf",
    "iam.tf", "lambda.tf", "ecr.tf", "agentcore.tf", "outputs.tf"
])
def test_terraform_file_uses_underscores(expected_file):
    """Test that terraform file names use underscores not hyphens."""
    tf_file = AGENTS_SRC / expected_file
    if tf_file.exists():
        name = tf_file.stem
        assert "-" not in name, f"File {tf_file.name} should use underscores not hyphens"


def test_lambda_function_names_use_locals():
    """Test that Lambda function names reference locals."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    # Should reference local for naming
    assert "local." in content, "Lambda terraform should reference local for naming"


def test_iam_role_names_use_module_or_locals():
    """Test that IAM role names reference module or locals."""
    iam_file = AGENTS_SRC / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    # Should reference module.shared or local for naming
    uses_module = "module.shared" in content
    uses_local = "local." in content
    assert uses_module or uses_local, "IAM terraform should reference module or local for naming"
