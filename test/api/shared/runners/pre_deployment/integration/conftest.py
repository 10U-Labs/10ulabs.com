"""Pytest fixtures for api/shared/runners pre-deployment integration tests.

These tests follow the 5-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""

import pytest
from repo_utils import REPO_ROOT

pytest_plugins = ['test_fixtures.aws']


API_SHARED_RUNNERS_SRC = REPO_ROOT / "src" / "api" / "shared" / "runners"

STATE_KEY = "api/shared/runners/terraform.tfstate"


@pytest.fixture(scope="session")
def runners_state_key():
    """Provide the terraform state key for api_shared_runners."""
    return STATE_KEY


@pytest.fixture(scope="session")
def api_shared_runners_src():
    """Provide path to api_shared_runners source directory."""
    return API_SHARED_RUNNERS_SRC
