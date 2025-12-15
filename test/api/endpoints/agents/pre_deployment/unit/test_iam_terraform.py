"""Unit tests for agents IAM Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_iam_terraform_file_exists():
    """Verify iam.tf file exists."""
    iam_file = AGENTS_SRC / "iam.tf"
    assert iam_file.exists()


def test_agentcore_execution_role_exists():
    """Verify AgentCore execution role is defined."""
    iam_file = AGENTS_SRC / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "agentcore_execution"' in content


def test_webhook_lambda_role_exists():
    """Verify webhook Lambda role is defined."""
    iam_file = AGENTS_SRC / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "webhook_lambda"' in content


def test_bedrock_permissions_present():
    """Verify Bedrock permissions are present in IAM policy."""
    iam_file = AGENTS_SRC / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert "bedrock" in content.lower()


def test_kms_decrypt_permission_present():
    """Verify KMS decrypt permission is present for environment variables."""
    iam_file = AGENTS_SRC / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert "kms" in content.lower()
