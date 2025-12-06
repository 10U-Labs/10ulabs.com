"""Integration test fixtures for RTL runner images."""

import boto3
import pytest


@pytest.fixture
def ecr_client() -> boto3.client:
    """Return ECR client for image verification."""
    return boto3.client("ecr")
