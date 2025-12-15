"""Unit tests for health endpoint remote state contract.

These tests verify that all terraform_remote_state.api.outputs references
in health/lambda.tf exist in api/backend/outputs.tf.
"""
import re
from test.api.operational.health.conftest import HEALTH_SRC, REPO_ROOT

LAMBDA_FILE = HEALTH_SRC / "lambda.tf"
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
    """Tests for remote state output contract between health and api backend."""

    def test_all_api_remote_state_references_exist_in_backend_outputs(self):
        """Verify all api remote state references exist in backend outputs."""
        references = get_api_remote_state_references()
        outputs = get_api_backend_outputs()
        missing = references - outputs

        assert not missing, (
            f"health/lambda.tf references api backend outputs that don't exist: "
            f"{missing}. Add these outputs to src/api/backend/outputs.tf"
        )

    def test_vpc_id_output_exists_in_backend(self):
        """Verify vpc_id output exists in api backend (regression test)."""
        outputs = get_api_backend_outputs()

        assert 'vpc_id' in outputs, (
            "vpc_id output missing from api/backend/outputs.tf. "
            "This is required by the health endpoint for VPC validation."
        )

    def test_vpc_public_subnet_ids_output_exists_in_backend(self):
        """Verify vpc_public_subnet_ids output exists in api backend."""
        outputs = get_api_backend_outputs()

        assert 'vpc_public_subnet_ids' in outputs

    def test_runner_security_group_id_output_exists_in_backend(self):
        """Verify runner_security_group_id output exists in api backend."""
        outputs = get_api_backend_outputs()

        assert 'runner_security_group_id' in outputs
