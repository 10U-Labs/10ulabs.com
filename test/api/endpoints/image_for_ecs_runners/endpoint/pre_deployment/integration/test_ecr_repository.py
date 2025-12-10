"""Tests to validate ECR repository dependencies before endpoint deployment.

These tests verify that the ECR repository exists and is accessible
before attempting to deploy the Lambda handler.

Five-layer testing model:
- Layer 1: Authentication - Can we call AWS APIs?
- Layer 2: Authorization - Do we have permission to check resources?
- Layer 3: Existence - Does the ECR repository exist?
- Layer 4: Configuration - Is the repository configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""
from botocore.exceptions import ClientError, NoCredentialsError
import pytest


class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        try:
            sts_client.get_caller_identity()
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

    def test_02_can_call_sts_api(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        try:
            response = sts_client.get_caller_identity()
            assert "Account" in response
            assert "Arn" in response
        except ClientError as e:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: {e.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )


class TestECRRepositoryAuthorization:
    """Layer 2: Verify we have permission to check ECR repository."""

    def test_01_can_call_describe_repositories_api(self, ecr_client, ecr_repository_name):
        """Verify we have permission to call ecr:DescribeRepositories."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:DescribeRepositories on '{ecr_repository_name}'. "
                    "Check IAM policy."
                )
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pass  # Repository existence checked in next layer
            else:
                raise

    def test_02_can_call_list_images_api(self, ecr_client, ecr_repository_name):
        """Verify we have permission to call ecr:ListImages."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            ecr_client.list_images(repositoryName=ecr_repository_name, maxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:ListImages on '{ecr_repository_name}'. "
                    "Check IAM policy."
                )
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pass  # Repository existence checked in next layer
            else:
                raise


class TestECRRepositoryExistence:
    """Layer 3: Verify the ECR repository exists."""

    def test_01_repository_exists(self, ecr_client, ecr_repository_name):
        """Verify the ECR repository exists."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            assert len(response["repositories"]) == 1
            assert response["repositories"][0]["repositoryName"] == ecr_repository_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{ecr_repository_name}' does not exist. "
                    "Run terraform apply in src/api/shared/ecs_runner/"
                )
            raise

    def test_02_repository_arn_is_valid(self, ecr_client, ecr_repository_name):
        """Verify the ECR repository ARN is valid."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repo = response["repositories"][0]
            assert "repositoryArn" in repo
            assert ":ecr:" in repo["repositoryArn"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist - tested in existence layer")
            raise


class TestECRRepositoryConfiguration:
    """Layer 4: Verify the ECR repository is configured correctly."""

    def test_01_repository_has_uri(self, ecr_client, ecr_repository_name):
        """Verify the ECR repository has a URI."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repo = response["repositories"][0]
            assert "repositoryUri" in repo, (
                f"ECR repository '{ecr_repository_name}' missing repositoryUri"
            )
            assert repo["repositoryUri"], (
                f"ECR repository '{ecr_repository_name}' has empty repositoryUri"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist - tested in existence layer")
            raise

    def test_02_repository_uri_format_is_valid(self, ecr_client, ecr_repository_name):
        """Verify the ECR repository URI format is valid."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repo = response["repositories"][0]
            uri = repo.get("repositoryUri", "")
            assert ".ecr." in uri and ".amazonaws.com/" in uri
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist - tested in existence layer")
            raise


class TestECRRepositoryCapability:
    """Layer 5: Verify we can perform required operations on ECR repository."""

    def test_01_can_describe_images(self, ecr_client, ecr_repository_name):
        """Verify we can list images in the repository."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            ecr_client.describe_images(
                repositoryName=ecr_repository_name,
                maxResults=1
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:DescribeImages on '{ecr_repository_name}'. "
                    "The Lambda role needs ecr:DescribeImages permission."
                )
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist - tested in existence layer")
            raise

    def test_02_can_list_images(self, ecr_client, ecr_repository_name):
        """Verify we can list images in the repository."""
        if not ecr_repository_name:
            pytest.skip("ECR repository name not configured")
        try:
            ecr_client.list_images(
                repositoryName=ecr_repository_name,
                maxResults=1
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:ListImages on '{ecr_repository_name}'. "
                    "The Lambda role needs ecr:ListImages permission."
                )
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist - tested in existence layer")
            raise
