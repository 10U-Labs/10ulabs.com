"""Layer 5: Configuration tests for ECS runner image deployment.

These tests verify that prerequisite resources are configured correctly.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, configuration tests
verify settings and configuration - assumes existence tests passed.
"""
import pytest

from .conftest import BASE_IMAGE, BASE_TAG



class TestECRRepositoryConfiguration:
    """Verify ECR repository is configured correctly."""

    def test_ecr_repository_has_uri(self, ecr_repository_details):
        """Verify the ECR repository has a URI for pushing images."""
        assert ecr_repository_details.get("repositoryUri"), (
            f"ECR repository '{ecr_repository_details['repositoryName']}' missing repositoryUri. "
            "Repository may be corrupted."
        )

    def test_ecr_repository_has_registry_id(self, ecr_repository_details):
        """Verify the ECR repository has a registry ID."""
        assert ecr_repository_details.get("registryId"), (
            f"ECR repository '{ecr_repository_details['repositoryName']}' missing registryId. "
            "Repository may be corrupted."
        )


class TestBaseDockerImageConfiguration:
    """Verify base Docker image is configured correctly."""

    def test_base_image_supports_arm64(self, docker_hub_image_data):
        """Verify the base Docker image supports arm64 architecture."""
        images = docker_hub_image_data.get("images", [])
        architectures = [img.get("architecture") for img in images]
        assert "arm64" in architectures, (
            f"Base image {BASE_IMAGE}:{BASE_TAG} does not support arm64 architecture. "
            f"Available architectures: {architectures}. "
            "ECS runners require arm64 architecture."
        )

    def test_base_image_has_digest(self, docker_hub_image_data):
        """Verify the base Docker image has a digest."""
        assert docker_hub_image_data.get("digest"), (
            f"Base image {BASE_IMAGE}:{BASE_TAG} missing digest. "
            "Image may be corrupted or unavailable."
        )
