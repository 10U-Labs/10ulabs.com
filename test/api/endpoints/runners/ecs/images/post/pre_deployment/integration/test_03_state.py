"""Layer 3: State tests for ECS runner image deployment.

Since this is a Docker image workflow (not Terraform), these tests verify
ECR image state consistency rather than Terraform state. This detects:
- Orphaned 'available' tags from failed builds
- Inconsistent tag states that may cause deployment issues
"""
from botocore.exceptions import ClientError

import pytest

pytestmark = pytest.mark.layer(3)


class TestECRImageState:
    """Verify ECR image tags are in a consistent state."""

    def test_available_tag_not_orphaned(self, ecr_client, api_shared_ecr_outputs):
        """Verify 'available' tag is not orphaned from a failed build.

        If 'available' exists but 'stable' doesn't, it indicates a build
        completed but promotion failed, leaving the repository in an
        inconsistent state.
        """
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")

        available_exists = False
        stable_exists = False

        try:
            response = ecr_client.describe_images(
                repositoryName=repository_name,
                filter={"tagStatus": "TAGGED"}
            )
            for image in response.get("imageDetails", []):
                tags = image.get("imageTags", [])
                if "available" in tags:
                    available_exists = True
                if "stable" in tags:
                    stable_exists = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist yet")
            raise

        if available_exists and not stable_exists:
            pytest.fail(
                "ECR repository has 'available' tag but no 'stable' tag. "
                "This indicates a previous build completed but promotion failed. "
                "Run the promote_docker_image.py script to fix this state."
            )

    def test_no_duplicate_stable_digests(self, ecr_client, api_shared_ecr_outputs):
        """Verify only one image has the 'stable' tag.

        Multiple images with 'stable' tag would indicate a corrupt state.
        """
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")

        try:
            response = ecr_client.describe_images(
                repositoryName=repository_name,
                imageIds=[{"imageTag": "stable"}]
            )
            stable_images = response.get("imageDetails", [])
            if len(stable_images) > 1:
                digests = [img["imageDigest"] for img in stable_images]
                pytest.fail(
                    f"Multiple images have 'stable' tag: {digests}. "
                    "ECR should have exactly one stable image."
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ImageNotFoundException":
                pass  # No stable image is acceptable before first deployment
            elif e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("Repository does not exist yet")
            else:
                raise
