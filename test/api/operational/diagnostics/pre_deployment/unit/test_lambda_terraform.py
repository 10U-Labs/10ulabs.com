"""Unit tests for diagnostics endpoint Lambda Terraform configuration."""
from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC
from test_fixtures.terraform_tests import create_lambda_terraform_tests


LAMBDA_FILE = DIAGNOSTICS_SRC / "lambda.tf"

TestLambdaTerraform = create_lambda_terraform_tests(
    lambda_file=LAMBDA_FILE,
    handler_name="diagnostics_handler",
    description="Diagnostics endpoint for API",
)
