"""Pytest fixtures for api/common/networking pre-deployment integration tests.

These tests follow the 6-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Terraform state matches AWS reality
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations?
"""

import pytest
from repo_utils import REPO_ROOT

pytest_plugins = ['test_fixtures.aws']


API_SHARED_NETWORKING_SRC = REPO_ROOT / "src" / "api" / "shared" / "networking"

STATE_KEY = "api/common/networking/terraform.tfstate"


@pytest.fixture(scope="session")
def networking_state_key():
    """Provide the terraform state key for api_common_networking."""
    return STATE_KEY


@pytest.fixture(scope="session")
def api_common_networking_src():
    """Provide path to api_common_networking source directory."""
    return API_SHARED_NETWORKING_SRC


@pytest.fixture(scope="session")
def state_bucket_region(shared_config):
    """Provide the expected region for the state bucket."""
    return shared_config["aws_region"]
