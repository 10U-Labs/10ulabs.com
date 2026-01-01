"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""

from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
)
from terraform_config import extract_iam_role_names, extract_lambda_function_names
from repo_utils import REPO_ROOT

EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2"
IAM_FILE = EC2_RUNNER_SRC / "iam.tf"
LAMBDA_FILE = EC2_RUNNER_SRC / "lambda.tf"

IAM_ROLES = extract_iam_role_names(IAM_FILE)
LAMBDA_FUNCTIONS = extract_lambda_function_names(LAMBDA_FILE, use_handler_names=True)

TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)
TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
