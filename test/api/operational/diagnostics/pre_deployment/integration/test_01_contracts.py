from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import (
    create_remote_state_contract_tests,
    create_routing_wait_contract_tests,
    create_state_lock_contract_tests,
)


DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    endpoint_name="diagnostics",
    required_outputs=["api_gateway_id"],
)

test_group_names_the_state_file = create_state_lock_contract_tests(
    DIAGNOSTICS_SRC, "api_operational_diagnostics.yml"
)

TestRoutingWaitContract = create_routing_wait_contract_tests(
    "api_operational_diagnostics.yml"
)
