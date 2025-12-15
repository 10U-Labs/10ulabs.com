"""Unit tests for agents ECR Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_ecr_terraform_file_exists():
    """Verify ecr.tf file exists."""
    ecr_file = AGENTS_SRC / "ecr.tf"
    assert ecr_file.exists()


def test_ecr_repository_resource_exists():
    """Verify ECR repository resource is defined."""
    ecr_file = AGENTS_SRC / "ecr.tf"
    with open(ecr_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecr_repository"' in content


def test_ecr_lifecycle_policy_exists():
    """Verify ECR lifecycle policy is defined."""
    ecr_file = AGENTS_SRC / "ecr.tf"
    with open(ecr_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecr_lifecycle_policy"' in content
