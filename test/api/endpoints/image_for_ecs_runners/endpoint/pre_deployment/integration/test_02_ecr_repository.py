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


@pytest.fixture(name="sts_identity", scope="module")
def sts_identity_fixture(sts_client):
    """Get STS caller identity."""
    try:
        return sts_client.get_caller_identity()
    except NoCredentialsError:
        pytest.fail(
            "No AWS credentials found. "
            "Configure credentials via environment variables, "
            "~/.aws/credentials, or IAM role."
        )
        return None  # Unreachable but satisfies pylint
    except ClientError as e:
        pytest.fail(
            f"Failed to call sts:GetCallerIdentity: {e.response['Error']['Message']}. "
            "Check AWS credentials are valid and not expired."
        )
        return None  # Unreachable but satisfies pylint


@pytest.fixture(name="ecr_repo", scope="module")
def ecr_repo_fixture(ecr_client, ecr_repository_name):
    """Get ECR repository details."""
    if not ecr_repository_name:
        pytest.fail("ECR repository name not configured")
        return None  # Unreachable but satisfies pylint
    try:
        response = ecr_client.describe_repositories(
            repositoryNames=[ecr_repository_name]
        )
        return response["repositories"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.fail(
                f"ECR repository '{ecr_repository_name}' does not exist. "
                "Run terraform apply in src/api/shared/ecs_runner/"
            )
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call ecr:DescribeRepositories on '{ecr_repository_name}'. "
                "Check IAM policy."
            )
        raise


class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_identity):
        """Verify AWS credentials are configured."""
        assert sts_identity is not None

    def test_02_identity_has_account(self, sts_identity):
        """Verify identity response has Account."""
        assert "Account" in sts_identity

    def test_03_identity_has_arn(self, sts_identity):
        """Verify identity response has Arn."""
        assert "Arn" in sts_identity


class TestECRRepositoryAuthorization:
    """Layer 2: Verify we have permission to check ECR repository."""

    def test_01_can_describe_repositories(self, ecr_repo):
        """Verify we can call ecr:DescribeRepositories."""
        assert ecr_repo is not None

    def test_02_can_list_images(self, ecr_client, ecr_repository_name):
        """Verify we have permission to call ecr:ListImages."""
        try:
            result = ecr_client.list_images(repositoryName=ecr_repository_name, maxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:ListImages on '{ecr_repository_name}'. "
                    "Check IAM policy."
                )
            raise

        assert "imageIds" in result


class TestECRRepositoryExistence:
    """Layer 3: Verify the ECR repository exists."""

    def test_01_repository_exists(self, ecr_repo, ecr_repository_name):
        """Verify the ECR repository exists."""
        assert ecr_repo["repositoryName"] == ecr_repository_name

    def test_02_repository_has_arn(self, ecr_repo):
        """Verify the ECR repository has ARN."""
        assert "repositoryArn" in ecr_repo

    def test_03_repository_arn_contains_ecr(self, ecr_repo):
        """Verify the ECR repository ARN contains :ecr:."""
        assert ":ecr:" in ecr_repo["repositoryArn"]


class TestECRRepositoryConfiguration:
    """Layer 4: Verify the ECR repository is configured correctly."""

    def test_01_repository_has_uri(self, ecr_repo):
        """Verify the ECR repository has repositoryUri field."""
        assert "repositoryUri" in ecr_repo

    def test_02_repository_uri_not_empty(self, ecr_repo):
        """Verify the ECR repository URI is not empty."""
        assert ecr_repo["repositoryUri"]

    def test_03_repository_uri_contains_ecr(self, ecr_repo):
        """Verify the ECR repository URI contains .ecr."""
        assert ".ecr." in ecr_repo["repositoryUri"]

    def test_04_repository_uri_contains_amazonaws(self, ecr_repo):
        """Verify the ECR repository URI contains .amazonaws.com."""
        assert ".amazonaws.com/" in ecr_repo["repositoryUri"]


class TestECRRepositoryCapability:
    """Layer 5: Verify we can perform required operations on ECR repository."""

    def test_01_can_describe_images(self, ecr_client, ecr_repository_name):
        """Verify we can describe images in the repository."""
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
            raise

        assert True

    def test_02_can_list_images(self, ecr_client, ecr_repository_name):
        """Verify we can list images in the repository."""
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
            raise

        assert True
