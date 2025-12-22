"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(3)


def _check_service_can_assume_role(trust_policy, service_name):
    """Check if a service can assume a role based on trust policy."""
    statements = trust_policy.get("Statement", [])
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        principals = statement.get("Principal", {})
        service = principals.get("Service", [])
        if isinstance(service, str):
            service = [service]
        if service_name in service:
            return True
    return False


class TestLambdaExecutionRole:
    """Verify Lambda execution role wiring."""

    def test_lambda_has_execution_role_key(self, lambda_function):
        """Verify Lambda function has Role key in configuration."""
        assert "Role" in lambda_function

    def test_lambda_has_execution_role_value(self, lambda_function):
        """Verify Lambda function execution role is not empty."""
        assert lambda_function.get("Role")

    def test_lambda_role_starts_with_iam_arn(self, lambda_function):
        """Verify Lambda execution role starts with IAM ARN prefix."""
        role_arn = lambda_function.get("Role", "")
        assert role_arn.startswith("arn:aws:iam::"), (
            f"Lambda role '{role_arn}' is not a valid IAM ARN"
        )

    def test_lambda_role_contains_role_path(self, lambda_function):
        """Verify Lambda execution role ARN contains :role/ path."""
        role_arn = lambda_function.get("Role", "")
        assert ":role/" in role_arn, (
            f"Lambda role '{role_arn}' does not appear to be a role ARN"
        )

    def test_lambda_role_exists(self, iam_client, lambda_function):
        """Verify the Lambda execution role exists in IAM."""
        role_arn = lambda_function.get("Role", "")
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

    def test_lambda_role_can_be_assumed_by_lambda(self, iam_client, lambda_function):
        """Verify the Lambda execution role has a trust policy for Lambda service."""
        role_arn = lambda_function.get("Role", "")
        role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

        if not role_name:
            pytest.skip("Could not extract role name from Lambda configuration")

        try:
            response = iam_client.get_role(RoleName=role_name)
            trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
            can_assume = _check_service_can_assume_role(
                trust_policy, "lambda.amazonaws.com"
            )

            assert can_assume, (
                f"Role '{role_name}' trust policy does not allow Lambda to assume it"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Role '{role_name}' does not exist")
            raise


class TestECSTaskRole:
    """Verify ECS task role wiring."""

    def test_ecs_task_role_exists(self, iam_client, ecs_task_role_name):
        """Verify the ECS task role exists."""
        if not ecs_task_role_name:
            pytest.skip("ecs_task_role_name not configured")
        try:
            response = iam_client.get_role(RoleName=ecs_task_role_name)
            assert response.get("Role") is not None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"ECS task role '{ecs_task_role_name}' does not exist in IAM."
                )
            raise

    def test_ecs_task_role_can_be_assumed_by_ecs(self, iam_client, ecs_task_role_name):
        """Verify the ECS task role has a trust policy for ECS tasks service."""
        if not ecs_task_role_name:
            pytest.skip("ecs_task_role_name not configured")

        try:
            response = iam_client.get_role(RoleName=ecs_task_role_name)
            trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
            can_assume = _check_service_can_assume_role(
                trust_policy, "ecs-tasks.amazonaws.com"
            )

            assert can_assume, (
                f"Role '{ecs_task_role_name}' trust policy does not allow "
                "ECS tasks to assume it"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Role '{ecs_task_role_name}' does not exist")
            raise
