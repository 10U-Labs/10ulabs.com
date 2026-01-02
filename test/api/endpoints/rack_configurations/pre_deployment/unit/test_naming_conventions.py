"""Unit tests to verify IAM role and Lambda function names use PascalCase."""
from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
)
from repo_utils import REPO_ROOT
from terraform_config import extract_iam_role_names, extract_lambda_function_names

RACK_DESIGNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_designer"

IAM_ROLES = (
    extract_iam_role_names(RACK_DESIGNER_SRC / "iam.tf")
    + extract_iam_role_names(RACK_DESIGNER_SRC / "analytics.tf")
)
LAMBDA_FUNCTIONS = (
    extract_lambda_function_names(RACK_DESIGNER_SRC / "lambda.tf", use_handler_names=True)
    + extract_lambda_function_names(RACK_DESIGNER_SRC / "analytics.tf", use_handler_names=True)
)

if IAM_ROLES:
    TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)

if LAMBDA_FUNCTIONS:
    TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
