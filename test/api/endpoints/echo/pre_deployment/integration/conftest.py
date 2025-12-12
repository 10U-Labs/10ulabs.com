"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (api_backend_outputs, ecs_runner_outputs, apigateway_client)
are inherited from test/api/conftest.py.
"""
import boto3
import pytest


@pytest.fixture(scope="session")
def iam_client(aws_region):
    """Create an IAM client."""
    return boto3.client("iam", region_name=aws_region)
