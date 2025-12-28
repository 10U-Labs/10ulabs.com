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

ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs"

IAM_ROLES = (
    extract_iam_role_names(ECS_RUNNER_SRC / "iam.tf")
    + extract_iam_role_names(ECS_RUNNER_SRC / "ecs_iam.tf")
)
LAMBDA_FUNCTIONS = extract_lambda_function_names(
    ECS_RUNNER_SRC / "lambda.tf", use_handler_names=True
)

assert IAM_ROLES, "Failed to extract IAM roles from ecs_runner Terraform files"
assert LAMBDA_FUNCTIONS, "Failed to extract Lambda functions from ecs_runner Terraform files"

TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)
TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
