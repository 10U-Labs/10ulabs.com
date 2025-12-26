"""Pytest fixtures for runners/ec2/images e2e tests.

E2E tests verify full user journeys by making HTTP requests to the API.
"""
import pytest


@pytest.fixture(name="amis_endpoint", scope="module")
def amis_endpoint_fixture(api_url) -> str:
    """Return the endpoint URL for listing AMIs."""
    return f"{api_url}/v1/runners/ec2/images"


@pytest.fixture(name="latest_ami_endpoint", scope="module")
def latest_ami_endpoint_fixture(api_url) -> str:
    """Return the endpoint URL for getting the latest AMI."""
    return f"{api_url}/v1/runners/ec2/images/latest"
