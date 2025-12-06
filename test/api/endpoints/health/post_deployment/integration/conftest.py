"""Pytest fixtures for health endpoint integration tests."""
import boto3
import pytest


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    """Create a Lambda client for the test region."""
    return boto3.client("lambda", region_name=aws_region)
