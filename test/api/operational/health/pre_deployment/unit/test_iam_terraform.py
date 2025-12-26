"""Unit tests for health endpoint IAM Terraform configuration."""
from test.api.operational.health.conftest import HEALTH_SRC
from test_fixtures.terraform_tests import create_iam_terraform_tests


IAM_FILE = HEALTH_SRC / "iam.tf"

TestIAMTerraform = create_iam_terraform_tests(
    iam_file=IAM_FILE,
    handler_name="health_handler",
)
