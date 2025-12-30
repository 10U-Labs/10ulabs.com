"""Unit tests for health endpoint remote state contract.

These tests verify that all terraform_remote_state.api.outputs references
in health/lambda.tf exist in api/backend/outputs.tf.
"""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=HEALTH_SRC,
    endpoint_name="health",
    required_outputs=[
        "vpc_id",
        "public_subnets_ids",
        "security_group_id_for_runners",
    ],
)
