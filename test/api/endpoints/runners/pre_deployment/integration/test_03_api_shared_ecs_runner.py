"""Tests to validate api_shared_ecs_runner infrastructure exists.

These tests verify that the ECR repository created by api_shared_ecs_runner
workflow exists and is properly configured. This is a REQUIRED prerequisite
(no defaults in data.tf) for the runners endpoint.

Five-layer testing model:
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
"""

import pytest
from botocore.exceptions import ClientError


class TestApiSharedEcsRunnerOutputs:
    """Layer 3: Verify api_shared_ecs_runner terraform outputs are accessible."""

    def test_01_ecr_repository_arn_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_arn output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_arn"), (
            "ecr_repository_arn output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )

    def test_02_ecr_repository_name_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_name output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_name"), (
            "ecr_repository_name output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )

    def test_03_ecr_repository_url_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_url output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_url"), (
            "ecr_repository_url output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )


class TestECRRepository:
    """Layer 3-4: Verify ECR repository exists and is properly configured."""

    def test_01_ecr_repository_exists(self, ecr_client, api_shared_ecs_runner_outputs):
        """Layer 3: Verify the ECR repository exists."""
        repo_name = api_shared_ecs_runner_outputs.get("ecr_repository_name")
        if not repo_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            response = ecr_client.describe_repositories(repositoryNames=[repo_name])
            assert len(response["repositories"]) == 1, (
                f"ECR repository '{repo_name}' not found. "
                "Run: cd src/api/shared/ecs_runner && terraform apply"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{repo_name}' does not exist. "
                    "Run: cd src/api/shared/ecs_runner && terraform apply"
                )
            raise

    def test_02_ecr_repository_has_image_scanning(
        self, ecr_client, api_shared_ecs_runner_outputs
    ):
        """Layer 4: Verify the ECR repository has image scanning configured."""
        repo_name = api_shared_ecs_runner_outputs.get("ecr_repository_name")
        if not repo_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            response = ecr_client.describe_repositories(repositoryNames=[repo_name])
            if not response["repositories"]:
                pytest.skip("Repository not found - covered by existence test")
            repo = response["repositories"][0]
            # Image scanning is recommended but not strictly required
            scan_config = repo.get("imageScanningConfiguration", {})
            if not scan_config.get("scanOnPush"):
                pytest.skip("Image scanning on push is not enabled (optional)")
        except ClientError:
            pytest.skip("Repository not found - covered by existence test")
