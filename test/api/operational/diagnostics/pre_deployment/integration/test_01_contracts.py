"""Layer 1: Contract tests for diagnostics endpoint pre-deployment.

Tests that local files that must work together are compatible. No AWS calls.
These tests verify cross-file contracts before any AWS operations.

Seven-layer testing model:
- Layer 1: Contracts - Local files are compatible
"""

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests



DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    endpoint_name="diagnostics",
    required_outputs=["api_gateway_id"],
)
