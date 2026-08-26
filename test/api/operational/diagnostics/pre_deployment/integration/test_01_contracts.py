from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests


DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    endpoint_name="diagnostics",
    required_outputs=["api_gateway_id"],
)
