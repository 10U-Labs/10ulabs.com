"""Layer 4: Existence tests for ECS runner image deployment.

These tests verify that prerequisite resources exist.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, existence tests verify
resources exist - assumes state tests passed.
"""
import pytest
import requests

from .conftest import BASE_IMAGE, BASE_TAG



class TestTerraformOutputsExist:
    """Verify terraform outputs from api_common_ecr are accessible."""

    def test_repository_name_output_exists(self, api_common_ecr_outputs):
        """Verify repository_name output is available."""
        assert api_common_ecr_outputs.get("repository_name"), (
            "repository_name output not found in api_common_ecr. "
            "Run terraform apply in src/api/common/ecr/"
        )

    def test_repository_url_output_exists(self, api_common_ecr_outputs):
        """Verify repository_url output is available."""
        assert api_common_ecr_outputs.get("repository_url"), (
            "repository_url output not found in api_common_ecr. "
            "Run terraform apply in src/api/common/ecr/"
        )

    def test_repository_arn_output_exists(self, api_common_ecr_outputs):
        """Verify repository_arn output is available."""
        assert api_common_ecr_outputs.get("repository_arn"), (
            "repository_arn output not found in api_common_ecr. "
            "Run terraform apply in src/api/common/ecr/"
        )


class TestECRRepositoryExists:
    """Verify ECR repository exists."""

    def test_ecr_repository_exists(self, ecr_repository_details, api_common_ecr_outputs):
        """Verify the ECR repository exists in AWS."""
        assert ecr_repository_details["repositoryName"] == api_common_ecr_outputs["repository_name"]

    def test_ecr_repository_is_accessible(self, ecr_repository_details):
        """Verify the ECR repository is accessible."""
        assert ecr_repository_details.get("repositoryArn"), (
            "ECR repository exists but ARN is not accessible"
        )


class TestBaseDockerImageExists:
    """Verify base Docker image exists on Docker Hub."""

    def test_base_image_exists_on_docker_hub(self):
        """Verify the base Docker image exists on Docker Hub."""
        url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
        response = requests.get(url, timeout=30)
        assert response.status_code == 200, (
            f"Base image {BASE_IMAGE}:{BASE_TAG} not found on Docker Hub. "
            f"Status: {response.status_code}. "
            "Check that the image name and tag are correct."
        )

    def test_base_image_tag_matches(self, docker_hub_image_data):
        """Verify the Docker Hub API returns the correct tag."""
        assert docker_hub_image_data.get("name") == BASE_TAG, (
            f"Tag mismatch: expected {BASE_TAG}, got {docker_hub_image_data.get('name')}"
        )
