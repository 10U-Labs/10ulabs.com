"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(3)


def test_lambda_has_execution_role_key(lambda_config):
    """Verify Lambda function has Role key in configuration."""
    assert "Role" in lambda_config


def test_lambda_has_execution_role_value(lambda_config):
    """Verify Lambda function execution role is not empty."""
    assert lambda_config.get("Role")


def test_lambda_role_starts_with_iam_arn(lambda_config):
    """Verify Lambda execution role starts with IAM ARN prefix."""
    role_arn = lambda_config.get("Role", "")
    assert role_arn.startswith("arn:aws:iam::"), (
        f"Lambda role '{role_arn}' is not a valid IAM ARN"
    )


def test_lambda_role_contains_role_path(lambda_config):
    """Verify Lambda execution role ARN contains :role/ path."""
    role_arn = lambda_config.get("Role", "")
    assert ":role/" in role_arn, (
        f"Lambda role '{role_arn}' does not appear to be a role ARN"
    )


def test_lambda_role_exists(iam_client, lambda_config):
    """Verify the Lambda execution role exists in IAM."""
    role_arn = lambda_config.get("Role", "")
    role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

    if not role_name:
        pytest.fail("Could not extract role name from Lambda configuration")

    try:
        response = iam_client.get_role(RoleName=role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"Lambda execution role '{role_name}' does not exist in IAM. "
                "The Lambda is configured with a non-existent role."
            )
        raise


def test_lambda_role_can_be_assumed_by_lambda(iam_client, lambda_config):
    """Verify the Lambda execution role has a trust policy for Lambda service."""
    role_arn = lambda_config.get("Role", "")
    role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

    if not role_name:
        pytest.skip("Could not extract role name from Lambda configuration")

    try:
        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
        statements = trust_policy.get("Statement", [])

        lambda_can_assume = False
        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue
            principals = statement.get("Principal", {})
            service = principals.get("Service", [])
            if isinstance(service, str):
                service = [service]
            if "lambda.amazonaws.com" in service:
                lambda_can_assume = True
                break

        assert lambda_can_assume, (
            f"Role '{role_name}' trust policy does not allow Lambda to assume it"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.skip(f"Role '{role_name}' does not exist")
        raise
