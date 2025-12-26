"""Unit tests for diagnostics endpoint IAM Terraform configuration."""
from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC
from test_fixtures.terraform_tests import create_iam_terraform_tests


IAM_FILE = DIAGNOSTICS_SRC / "iam.tf"

TestIAMTerraform = create_iam_terraform_tests(
    iam_file=IAM_FILE,
    handler_name="diagnostics_handler",
)
