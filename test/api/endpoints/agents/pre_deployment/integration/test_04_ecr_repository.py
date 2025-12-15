"""Layer 3-4 tests: ECR Repository for Agent Runtime.

The agents endpoint runtime container images are stored in ECR.
This tests that the ECR repository exists and is properly configured.

Five-layer testing model:
- Layer 3: Existence - Does the ECR repository exist?
- Layer 4: Configuration - Is the repository configured correctly?
"""

import pytest
from botocore.exceptions import ClientError


class TestECRRepositoryExistence:
    """Layer 3: Verify the ECR repository exists."""

    def test_01_agents_ecr_repository_exists(self, ecr_client, ecr_repository_name):
        """Verify the agents ECR repository exists."""
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repos = response.get("repositories", [])
            assert len(repos) > 0, (
                f"ECR repository '{ecr_repository_name}' not found."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{ecr_repository_name}' does not exist. "
                    "Run the agents_infrastructure workflow to create it."
                )
            raise


class TestECRRepositoryConfiguration:
    """Layer 4: Verify the ECR repository is configured correctly."""

    def test_01_ecr_repository_has_lifecycle_policy(
        self, ecr_client, ecr_repository_name
    ):
        """Verify the ECR repository has a lifecycle policy configured."""
        try:
            response = ecr_client.get_lifecycle_policy(
                repositoryName=ecr_repository_name
            )
            policy_text = response.get("lifecyclePolicyText", "")
            assert policy_text, (
                f"ECR repository '{ecr_repository_name}' should have a lifecycle policy "
                "to manage image retention."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "LifecyclePolicyNotFoundException":
                pytest.fail(
                    f"ECR repository '{ecr_repository_name}' has no lifecycle policy. "
                    "Add a lifecycle policy to manage image retention."
                )
            if code == "RepositoryNotFoundException":
                pytest.skip("ECR repository not found - covered by existence test")
            raise

    def test_02_ecr_repository_has_scan_on_push(self, ecr_client, ecr_repository_name):
        """Verify the ECR repository has image scanning enabled on push."""
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repos = response.get("repositories", [])
            if repos:
                scan_config = repos[0].get("imageScanningConfiguration", {})
                scan_on_push = scan_config.get("scanOnPush", False)
                assert scan_on_push, (
                    f"ECR repository '{ecr_repository_name}' should have "
                    "image scanning enabled on push for security."
                )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository not found - covered by existence test")
            raise

    def test_03_ecr_repository_is_named_correctly(
        self, ecr_client, ecr_repository_name
    ):
        """Verify the ECR repository name is lowercase."""
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repository_name]
            )
            repos = response.get("repositories", [])
            if repos:
                name = repos[0].get("repositoryName", "")
                assert name == name.lower(), (
                    f"ECR repository name '{name}' should be lowercase."
                )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository not found - covered by existence test")
            raise
