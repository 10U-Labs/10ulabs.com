"""Unit tests for diagnostics endpoint remote state contract.

These tests verify that all terraform_remote_state.api.outputs references
in diagnostics/lambda.tf exist in api/backend/outputs.tf.
"""
import re

from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC
from repo_utils import REPO_ROOT

LAMBDA_FILE = DIAGNOSTICS_SRC / "lambda.tf"
API_BACKEND_OUTPUTS_FILE = REPO_ROOT / "src" / "api" / "backend" / "outputs.tf"


def get_api_remote_state_references():
    """Extract all data.terraform_remote_state.api.outputs.X references."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    pattern = r'data\.terraform_remote_state\.api\.outputs\.(\w+)'
    return set(re.findall(pattern, content))


def get_api_backend_outputs():
    """Extract all output names from api/backend/outputs.tf."""
    with open(API_BACKEND_OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"(\w+)"'
    return set(re.findall(pattern, content))


class TestRemoteStateContract:
    """Tests for remote state output contract between diagnostics and api backend."""

    def test_all_api_remote_state_references_exist_in_backend_outputs(self):
        """Verify all api remote state references exist in backend outputs."""
        references = get_api_remote_state_references()
        outputs = get_api_backend_outputs()
        missing = references - outputs

        assert not missing, (
            f"diagnostics/lambda.tf references api backend outputs that don't exist: "
            f"{missing}. Add these outputs to src/api/backend/outputs.tf"
        )

    def test_api_gateway_rest_api_id_output_exists_in_backend(self):
        """Verify api_gateway_rest_api_id output exists in api backend."""
        outputs = get_api_backend_outputs()

        assert 'api_gateway_rest_api_id' in outputs, (
            "api_gateway_rest_api_id output missing from api/backend/outputs.tf. "
            "This is required by the diagnostics endpoint for API Gateway permission."
        )
