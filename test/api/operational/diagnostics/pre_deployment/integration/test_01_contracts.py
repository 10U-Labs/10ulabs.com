import re

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests


DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"
DIAGNOSTICS_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "api_operational_diagnostics.yml"
)

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    endpoint_name="diagnostics",
    required_outputs=["api_gateway_id"],
)


def test_backend_state_key_matches_workflow_concurrency_group() -> None:
    backend_content = (DIAGNOSTICS_SRC / "backend.tf").read_text()
    workflow_content = DIAGNOSTICS_WORKFLOW.read_text()

    key_match = re.search(
        r'^\s*key\s*=\s*"([^"]+)"', backend_content, re.MULTILINE
    )
    group_match = re.search(
        r'^\s*group:\s*(\S+)', workflow_content, re.MULTILINE
    )
    state_key = key_match.group(1) if key_match else "<backend.tf declares no key>"
    group = (
        group_match.group(1) if group_match
        else "<api_operational_diagnostics.yml declares no concurrency group>"
    )

    assert state_key == group, (
        f"backend.tf key '{state_key}' and api_operational_diagnostics.yml "
        f"concurrency group '{group}' have drifted, so the lock protects a "
        f"state file the workflow is not writing"
    )
