"""Shared fixtures for sessions endpoint tests.

Contains fixtures used by both pre-deployment and post-deployment tests.
"""
import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
API_COMMON_ROUTING_PATH = REPO_ROOT / "src" / "api" / "common" / "routing"


@pytest.fixture(scope="module")
def sessions_terraform_initialized():
    """Initialize terraform for sessions state access."""
    return terraform_init(SESSIONS_SRC_PATH)


@pytest.fixture(scope="module")
def api_common_routing_initialized():
    """Initialize terraform for api_common_routing state access."""
    return terraform_init(API_COMMON_ROUTING_PATH)


@pytest.fixture(scope="module")
def api_gateway_id(request):
    """Get API Gateway ID from api_common_routing outputs."""
    if not request.getfixturevalue("api_common_routing_initialized"):
        pytest.skip("Terraform init failed for api_common_routing")
    return terraform_output(API_COMMON_ROUTING_PATH, "api_gateway_id")
