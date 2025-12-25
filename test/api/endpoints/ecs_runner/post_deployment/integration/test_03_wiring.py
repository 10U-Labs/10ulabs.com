"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import (
    check_service_can_assume_role,
    create_lambda_execution_role_wiring_tests,
)

pytestmark = pytest.mark.layer(3)


# Create Lambda execution role wiring tests using lambda_function fixture
TestLambdaExecutionRole = create_lambda_execution_role_wiring_tests(
    fixture_name="lambda_function"
)


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
            can_assume = check_service_can_assume_role(
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
