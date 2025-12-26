"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest

pytestmark = pytest.mark.layer(1)


class TestLambdaExistence:
    """Verify Lambda function exists."""

    def test_lambda_function_exists(self, lambda_function):
        """Verify the EcsRunnerHandler Lambda function exists."""
        assert lambda_function is not None

    def test_lambda_function_has_arn(self, lambda_function):
        """Verify the Lambda function has an ARN."""
        assert "FunctionArn" in lambda_function

    def test_lambda_function_has_role(self, lambda_function):
        """Verify the Lambda function has a Role configured."""
        assert "Role" in lambda_function


class TestECSClusterExistence:
    """Verify ECS cluster exists."""

    def test_ecs_cluster_exists(self, ecs_client, cluster_name):
        """Verify the ECS cluster exists."""
        if not cluster_name:
            pytest.skip("cluster_name not configured")
        response = ecs_client.describe_clusters(clusters=[cluster_name])
        assert len(response['clusters']) == 1

    def test_ecs_cluster_is_active(self, ecs_client, cluster_name):
        """Verify the ECS cluster is in ACTIVE status."""
        if not cluster_name:
            pytest.skip("cluster_name not configured")
        response = ecs_client.describe_clusters(clusters=[cluster_name])
        assert response['clusters'][0]['status'] == 'ACTIVE'


class TestECSTaskDefinitionExistence:
    """Verify ECS task definition exists."""

    def test_ecs_task_definition_exists(self, task_definition):
        """Verify the ECS task definition exists."""
        if task_definition is None:
            pytest.skip(
                "ECS task definitions not deployed "
                "(managed by endpoint_v1_ecs_runner.yml workflow)"
            )
        assert task_definition is not None

    def test_ecs_task_definition_has_arn(self, task_definition):
        """Verify the task definition has an ARN."""
        if task_definition is None:
            pytest.skip("ECS task definition not deployed")
        assert "taskDefinitionArn" in task_definition


class TestCloudWatchLogGroupExistence:
    """Verify CloudWatch log groups exist."""

    def test_lambda_log_group_exists(self, lambda_log_group):
        """Verify CloudWatch log group for Lambda handler exists."""
        assert lambda_log_group["exists"], (
            f"CloudWatch log group '{lambda_log_group['name']}' does not exist"
        )

    def test_ecs_log_group_exists(self, ecs_log_group):
        """Verify CloudWatch log group for ECS tasks exists."""
        assert ecs_log_group["exists"], (
            f"CloudWatch log group '{ecs_log_group['name']}' does not exist"
        )
