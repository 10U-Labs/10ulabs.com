"""Unit tests for diagnostics endpoint backend Terraform configuration."""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_backend_terraform_tests

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestBackendTerraform = create_backend_terraform_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    state_key="diagnostics/terraform.tfstate",
)
