"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).

Lambda function and IAM role names are extracted from Terraform files (single source of truth).
"""
from pathlib import Path

import pytest

from naming_conventions import validate_name
from terraform_config import extract_iam_role_names, extract_lambda_function_names

REPO_ROOT = Path(__file__).resolve().parents[6]
RUNNERS_TF_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


def _get_iam_role_names():
    """Get IAM role names from Terraform (single source of truth)."""
    return list(extract_iam_role_names(RUNNERS_TF_DIR / "iam.tf"))


def _get_lambda_function_names():
    """Get Lambda function names from Terraform (single source of truth)."""
    return list(extract_lambda_function_names(
        RUNNERS_TF_DIR / "lambda.tf", use_handler_names=True
    ))


@pytest.mark.parametrize(
    "resource_name,role_name",
    _get_iam_role_names(),
    ids=[name for name, _ in _get_iam_role_names()],
)
def test_iam_role_name_is_pascalcase(iam_client, resource_name, role_name):
    """Verify IAM role name uses PascalCase."""
    _ = resource_name  # Used for test parametrization IDs
    try:
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )
    except iam_client.exceptions.NoSuchEntityException:
        pytest.skip(f"IAM role '{role_name}' not deployed")


@pytest.mark.parametrize(
    "resource_name,function_name",
    _get_lambda_function_names(),
    ids=[name for name, _ in _get_lambda_function_names()],
)
def test_lambda_function_name_is_pascalcase(lambda_client, resource_name, function_name):
    """Verify Lambda function name uses PascalCase."""
    _ = resource_name  # Used for test parametrization IDs
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function '{function_name}' not deployed")
