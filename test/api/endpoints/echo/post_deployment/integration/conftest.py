"""Pytest fixtures for echo integration tests."""
from test.api.conftest import skip_if_endpoint_not_deployed

import boto3
import pytest

# Re-export for local imports
__all__ = ['skip_if_endpoint_not_deployed']


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    """Create Lambda client for AWS region."""
    return boto3.client("lambda", region_name=aws_region)
