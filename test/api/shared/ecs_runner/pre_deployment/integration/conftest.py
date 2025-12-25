"""Pytest fixtures for api/shared/ecs_runner pre-deployment integration tests.

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

pytest_plugins = ['pytest_layers', 'test_fixtures.aws']


API_SHARED_ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"

STATE_KEY = "api/shared/ecs_runner/terraform.tfstate"


@pytest.fixture(scope="session")
def ecs_runner_state_key():
    """Provide the terraform state key for api_shared_ecs_runner."""
    return STATE_KEY


@pytest.fixture(scope="session")
def api_shared_ecs_runner_src():
    """Provide path to api_shared_ecs_runner source directory."""
    return API_SHARED_ECS_RUNNER_SRC


@pytest.fixture(scope="session")
def state_bucket_region(shared_config):
    """Provide the expected region for the state bucket."""
    return shared_config["aws_region"]
