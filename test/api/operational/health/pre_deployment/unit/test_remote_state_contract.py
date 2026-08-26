from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=HEALTH_SRC,
    endpoint_name="health",
)
