"""Layer 6: Capability tests for ECS runner.

These tests verify we can perform required operations on ECS resources.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, capability tests verify
we can perform operations - assumes configuration tests passed.
"""
from botocore.exceptions import ClientError

import pytest

from test_fixtures.integration import handle_ecr_error
from .conftest import get_repository_name_or_skip



class TestECSCapability:
    """Verify we can perform required ECS operations."""

    def test_can_list_ecs_clusters(self, ecs_client):
        """Verify we can list ECS clusters."""
        try:
            response = ecs_client.list_clusters()
            assert "clusterArns" in response, (
                "ECS list_clusters response missing clusterArns. "
                "Cannot list ECS clusters."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to list ECS clusters: {e.response['Error']['Message']}. "
                "This is required to manage ECS runners."
            )

    def test_can_list_task_definitions(self, ecs_client):
        """Verify we can list ECS task definitions."""
        try:
            response = ecs_client.list_task_definitions(maxResults=1)
            assert "taskDefinitionArns" in response, (
                "ECS list_task_definitions response missing taskDefinitionArns. "
                "Cannot list ECS task definitions."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to list ECS task definitions: {e.response['Error']['Message']}. "
                "This is required to manage ECS runners."
            )

    def test_can_describe_task_definition(self, ecs_client):
        """Verify we can describe an ECS task definition."""
        try:
            # First list to get a task definition ARN
            list_response = ecs_client.list_task_definitions(
                familyPrefix="github-runner",
                maxResults=1
            )
            if not list_response.get("taskDefinitionArns"):
                pytest.skip("No github-runner task definitions found")
            task_def_arn = list_response["taskDefinitionArns"][0]
            # Then describe it
            response = ecs_client.describe_task_definition(
                taskDefinition=task_def_arn
            )
            assert "taskDefinition" in response, (
                "ECS describe_task_definition response missing taskDefinition."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecs:DescribeTaskDefinition. "
                    "This is required to manage ECS runners."
                )
            raise


class TestECRCapability:
    """Verify we can perform required ECR operations for ECS."""

    def test_can_get_ecr_authorization_data(self, ecr_client):
        """Verify we can get ECR authorization data for docker pull."""
        try:
            response = ecr_client.get_authorization_token()
            assert response.get("authorizationData"), (
                "ECR returned empty authorization data. "
                "Cannot authenticate to pull Docker images for ECS tasks."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to get ECR authorization token: {e.response['Error']['Message']}. "
                "This is required to pull Docker images for ECS tasks."
            )

    def test_can_describe_images_in_repository(self, ecr_client, api_common_ecr_outputs):
        """Verify we can describe images in the ECR repository."""
        repository_name = get_repository_name_or_skip(api_common_ecr_outputs)
        try:
            ecr_client.describe_images(
                repositoryName=repository_name,
                maxResults=1
            )
        except ClientError as e:
            handle_ecr_error(e, "ecr:DescribeImages", repository_name)


class TestCloudWatchLogsCapability:
    """Verify we can perform required CloudWatch Logs operations."""

    def test_can_describe_log_groups(self, logs_client):
        """Verify we can describe CloudWatch log groups."""
        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix="/ecs/github-runner",
                limit=1
            )
            assert "logGroups" in response, (
                "CloudWatch Logs describe_log_groups response missing logGroups."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to describe log groups: {e.response['Error']['Message']}. "
                "This is required to view ECS runner logs."
            )

    def test_can_get_log_events(self, logs_client):
        """Verify we can retrieve CloudWatch log events."""
        try:
            # First find the log group
            groups_response = logs_client.describe_log_groups(
                logGroupNamePrefix="/ecs/github-runner",
                limit=1
            )
            if not groups_response.get("logGroups"):
                pytest.skip("No /ecs/github-runner log group found")
            log_group_name = groups_response["logGroups"][0]["logGroupName"]
            # Then list streams
            streams_response = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                limit=1
            )
            if not streams_response.get("logStreams"):
                pytest.skip("No log streams found")
            log_stream_name = streams_response["logStreams"][0]["logStreamName"]
            # Finally get events
            logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                limit=1
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Log group or stream not found")
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call logs:GetLogEvents. "
                    "This is required to view ECS runner logs."
                )
            raise
