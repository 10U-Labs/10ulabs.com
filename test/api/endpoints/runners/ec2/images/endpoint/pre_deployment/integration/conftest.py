"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import (
    API_BACKEND_DIR,
    terraform_init,
    terraform_output,
)

import pytest

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_shared_routing state access."""
    return terraform_init(API_BACKEND_DIR)


@pytest.fixture(scope="session")
def api_shared_routing_outputs(request):
    """Get api_shared_routing terraform outputs for EC2 runner AMI.

    Note: This overrides the shared api_shared_routing_outputs fixture with
    EC2-runner-specific outputs.
    """
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_routing")
    return {
        "ec2_runner_ami_purpose_value": terraform_output(
            API_BACKEND_DIR, "ec2_runner_ami_purpose_value"
        ),
        "ec2_runner_ami_stable_tag": terraform_output(
            API_BACKEND_DIR, "ec2_runner_ami_stable_tag"
        ),
    }


@pytest.fixture(scope="session")
def ami_purpose_value(request):
    """Get the AMI purpose tag value."""
    outputs = request.getfixturevalue("api_shared_routing_outputs")
    return outputs.get("ec2_runner_ami_purpose_value", "")


@pytest.fixture(scope="session")
def ami_stable_tag(request):
    """Get the AMI stable tag name."""
    outputs = request.getfixturevalue("api_shared_routing_outputs")
    return outputs.get("ec2_runner_ami_stable_tag", "")
