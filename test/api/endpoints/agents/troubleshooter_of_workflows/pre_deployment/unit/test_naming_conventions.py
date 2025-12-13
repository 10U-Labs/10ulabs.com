"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from pathlib import Path

from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
)
from terraform_config import extract_iam_role_names, extract_lambda_function_names

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
TROUBLESHOOTER_SRC = (
    REPO_ROOT / "src" / "api" / "endpoints" / "agents" / "troubleshooter_of_workflows"
)

IAM_ROLES = extract_iam_role_names(TROUBLESHOOTER_SRC / "iam.tf")
LAMBDA_FUNCTIONS = extract_lambda_function_names(TROUBLESHOOTER_SRC / "lambda.tf")

assert IAM_ROLES, "Failed to extract IAM roles from troubleshooter_of_workflows iam.tf"
assert LAMBDA_FUNCTIONS, (
    "Failed to extract Lambda functions from troubleshooter_of_workflows lambda.tf"
)

TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)
TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
