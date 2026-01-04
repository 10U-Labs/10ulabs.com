"""Layer 4: Existence tests.

Verify prerequisite resources exist.
"""
import pytest



def test_ecr_repository_exists(ecr_repo, ecr_repository_name):
    """Verify the ECR repository exists."""
    assert ecr_repo["repositoryName"] == ecr_repository_name


def test_ecr_repository_has_arn(ecr_repo):
    """Verify the ECR repository has ARN."""
    assert "repositoryArn" in ecr_repo


def test_ecr_repository_arn_contains_ecr(ecr_repo):
    """Verify the ECR repository ARN contains :ecr:."""
    assert ":ecr:" in ecr_repo["repositoryArn"]
