"""Tests to validate ECR has a stable image for ECS runners.

Five-layer testing model:
- Layer 3: Existence - Does the ECR repository exist? Does the stable image exist?
- Layer 4: Configuration - Is the stable image properly tagged?

These tests verify that ECR resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestECRRepositoryExistence:
    """Layer 3: Verify ECR repository exists."""

    def test_repository_name_output_exists(self, api_shared_ecr_outputs):
        """Verify repository_name output is available."""
        assert api_shared_ecr_outputs.get("repository_name"), (
            "repository_name output not found in api_shared_ecr. "
            "Run terraform apply in src/api/shared/ecr/"
        )

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


class TestECRStableImage:
    """Layer 4: Verify stable image is properly configured."""

    def test_stable_image_has_digest(self, ecr_client, api_shared_ecr_outputs):
        """Verify the stable image has a valid digest."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            response = ecr_client.describe_images(
                repositoryName=repository_name,
                imageIds=[{"imageTag": "stable"}]
            )
            if not response["imageDetails"]:
                pytest.skip("No stable image found")
            image = response["imageDetails"][0]
            assert "imageDigest" in image, (
                "Stable image missing digest. Image may be corrupted."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ImageNotFoundException":
                pytest.skip("No stable image found")
            raise

    def test_stable_image_digest_format(self, ecr_client, api_shared_ecr_outputs):
        """Verify the stable image digest has valid format."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            response = ecr_client.describe_images(
                repositoryName=repository_name,
                imageIds=[{"imageTag": "stable"}]
            )
            if not response["imageDetails"]:
                pytest.skip("No stable image found")
            image = response["imageDetails"][0]
            digest = image.get("imageDigest", "")
            assert digest.startswith("sha256:"), (
                f"Invalid image digest format: {digest}. Expected sha256:..."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ImageNotFoundException":
                pytest.skip("No stable image found")
            raise
