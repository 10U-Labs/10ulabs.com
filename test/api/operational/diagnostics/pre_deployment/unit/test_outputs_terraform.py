"""Unit tests for diagnostics endpoint outputs Terraform configuration."""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_outputs_terraform_tests

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestOutputsTerraform = create_outputs_terraform_tests(
    endpoint_src=DIAGNOSTICS_SRC,
    required_outputs=["lambda_function_arn", "lambda_function_name", "log_group_name"],
)
