import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
API_COMMON_ROUTING_PATH = REPO_ROOT / "src" / "api" / "common" / "routing"


@pytest.fixture(scope="module")
def sessions_terraform_initialized():
    return terraform_init(SESSIONS_SRC_PATH)


@pytest.fixture(scope="module")
def api_common_routing_initialized():
    return terraform_init(API_COMMON_ROUTING_PATH)


@pytest.fixture(scope="module")
def api_gateway_id(request):
    if not request.getfixturevalue("api_common_routing_initialized"):
        pytest.skip("Terraform init failed for api_common_routing")
    return terraform_output(API_COMMON_ROUTING_PATH, "api_gateway_id")
