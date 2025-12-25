"""Unit tests for health endpoint backend Terraform configuration."""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_backend_terraform_tests

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

TestBackendTerraform = create_backend_terraform_tests(
    endpoint_src=HEALTH_SRC,
    state_key="health/terraform.tfstate",
)
