"""Tests to validate api_shared_ecr infrastructure exists.

Five-layer testing model:
- Layer 3: Existence - Does the ECR repository exist?

These tests verify that api_shared_ecr resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestAPISharedECROutputs:
    """Layer 3: Verify api_shared_ecr terraform outputs are accessible."""

    def test_repository_name_output_exists(self, api_shared_ecr_outputs):
        """Verify repository_name output is available."""
        assert api_shared_ecr_outputs.get("repository_name"), (
            "repository_name output not found in api_shared_ecr. "
            "Run terraform apply in src/api/shared/ecr/"
        )

    def test_repository_url_output_exists(self, api_shared_ecr_outputs):
        """Verify repository_url output is available."""
        assert api_shared_ecr_outputs.get("repository_url"), (
            "repository_url output not found in api_shared_ecr. "
            "Run terraform apply in src/api/shared/ecr/"
        )

    def test_repository_arn_output_exists(self, api_shared_ecr_outputs):
        """Verify repository_arn output is available."""
        assert api_shared_ecr_outputs.get("repository_arn"), (
            "repository_arn output not found in api_shared_ecr. "
            "Run terraform apply in src/api/shared/ecr/"
        )


class TestECRRepository:
    """Layer 3-4: Verify ECR repository exists and is configured."""

    def test_ecr_repository_exists(self, ecr_client, api_shared_ecr_outputs):
        """Verify the ECR repository exists in AWS."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            response = ecr_client.describe_repositories(repositoryNames=[repository_name])
            assert len(response["repositories"]) == 1, (
                f"Expected 1 repository, got {len(response['repositories'])}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{repository_name}' does not exist. "
                    "Run terraform apply in src/api/shared/ecr/"
                )
            raise

    def test_ecr_repository_has_uri(self, ecr_client, api_shared_ecr_outputs):
        """Verify the ECR repository has a URI for pushing images."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            response = ecr_client.describe_repositories(repositoryNames=[repository_name])
            if not response["repositories"]:
                pytest.skip("Repository does not exist")
            repo = response["repositories"][0]
            assert repo.get("repositoryUri"), (
                f"ECR repository '{repository_name}' missing repositoryUri. "
                "Repository may be corrupted."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist")
            raise
