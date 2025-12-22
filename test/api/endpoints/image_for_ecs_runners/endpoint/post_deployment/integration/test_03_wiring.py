"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(3)


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.skip("Lambda function not found")
    return matching[0]


@pytest.fixture(name="lambda_config", scope="module")
def lambda_config_fixture(lambda_client, lambda_function):
    """Get the Lambda function configuration."""
    return lambda_client.get_function_configuration(
        FunctionName=lambda_function["FunctionName"]
    )


def test_lambda_has_execution_role(lambda_config):
    """Verify Lambda function has an execution role configured."""
    assert "Role" in lambda_config
    assert lambda_config["Role"]


def test_lambda_role_is_valid_arn(lambda_config):
    """Verify Lambda execution role is a valid IAM role ARN."""
    role_arn = lambda_config.get("Role", "")
    assert role_arn.startswith("arn:aws:iam::"), (
        f"Lambda role '{role_arn}' is not a valid IAM ARN"
    )
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
