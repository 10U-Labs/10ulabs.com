"""Layer 5: Configuration tests.

Verify prerequisite resources are configured correctly.
"""
import pytest



def test_ecr_repository_has_uri(ecr_repo):
    """Verify the ECR repository has repositoryUri field."""
    assert "repositoryUri" in ecr_repo


def test_ecr_repository_uri_not_empty(ecr_repo):
    """Verify the ECR repository URI is not empty."""
    assert ecr_repo["repositoryUri"]


def test_ecr_repository_uri_contains_ecr(ecr_repo):
    """Verify the ECR repository URI contains .ecr."""
    assert ".ecr." in ecr_repo["repositoryUri"]


def test_ecr_repository_uri_contains_amazonaws(ecr_repo):
    """Verify the ECR repository URI contains .amazonaws.com."""
    assert ".amazonaws.com/" in ecr_repo["repositoryUri"]
