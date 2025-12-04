"""Pytest fixtures for simulation-soc integration tests."""
import boto3
import pytest


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    """Create a boto3 Lambda client for the given AWS region."""
    return boto3.client("lambda", region_name=aws_region)
