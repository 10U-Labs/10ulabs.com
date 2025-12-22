"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(1)


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.fail(
            "No Lambda function found matching 'ImageForEcsRunners'. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/"
        )
    return matching[0]


def test_lambda_function_exists(lambda_function):
    """Verify the ImageForEcsRunners Lambda function exists."""
    assert lambda_function is not None


def test_lambda_function_has_arn(lambda_function):
    """Verify the Lambda function has an ARN."""
    assert "FunctionArn" in lambda_function


def test_lambda_execution_role_exists(iam_client, lambda_function):
    """Verify the Lambda execution role exists."""
    role_name = f"{lambda_function['FunctionName']}ServiceRole"
    try:
        response = iam_client.get_role(RoleName=role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"Lambda execution role '{role_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/image_for_ecs_runners/"
            )
        raise
