"""Pytest fixtures for contact integration tests."""
import boto3
import pytest


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    """Create Lambda client for AWS region."""
    return boto3.client("lambda", region_name=aws_region)
