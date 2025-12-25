"""Unit tests for health endpoint outputs Terraform configuration."""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_outputs_terraform_tests

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

TestOutputsTerraform = create_outputs_terraform_tests(
    endpoint_src=HEALTH_SRC,
    required_outputs=["lambda_function_arn", "lambda_function_name"],
)
