"""Unit tests to verify IAM role and Lambda function names use PascalCase."""
from pathlib import Path

from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
)
from terraform_config import extract_iam_role_names, extract_lambda_function_names

SIMULATION_SOC_SRC = Path(__file__).parents[6] / "src" / "api" / "endpoints" / "simulation_soc"

IAM_ROLES = extract_iam_role_names(SIMULATION_SOC_SRC / "iam.tf")
LAMBDA_FUNCTIONS = extract_lambda_function_names(
    SIMULATION_SOC_SRC / "lambda.tf", use_handler_names=True
)

if IAM_ROLES:
    TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)

if LAMBDA_FUNCTIONS:
    TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
