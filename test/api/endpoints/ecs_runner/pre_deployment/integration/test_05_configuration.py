"""Layer 5: Configuration tests.

Verify prerequisite resources are configured correctly.
"""
from botocore.exceptions import ClientError
import pytest

from .conftest import get_repository_name_or_skip

pytestmark = pytest.mark.layer(5)


def _get_stable_image_or_skip(ecr_client, repository_name):
    """Get stable image details or skip test if not found."""
    try:
        response = ecr_client.describe_images(
            repositoryName=repository_name,
            imageIds=[{"imageTag": "stable"}]
        )
        if not response["imageDetails"]:
            pytest.skip("No stable image found")
        return response["imageDetails"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ImageNotFoundException":
            pytest.skip("No stable image found")
        raise


class TestECRStableImageConfiguration:
    """Verify stable image is properly configured."""

    def test_stable_image_has_digest(self, ecr_client, api_shared_ecr_outputs):
        """Verify the stable image has a valid digest."""
        repository_name = get_repository_name_or_skip(api_shared_ecr_outputs)
        image = _get_stable_image_or_skip(ecr_client, repository_name)
        assert "imageDigest" in image, (
            "Stable image missing digest. Image may be corrupted."
        )

    def test_stable_image_digest_format(self, ecr_client, api_shared_ecr_outputs):
        """Verify the stable image digest has valid format."""
        repository_name = get_repository_name_or_skip(api_shared_ecr_outputs)
        image = _get_stable_image_or_skip(ecr_client, repository_name)
        digest = image.get("imageDigest", "")
        assert digest.startswith("sha256:"), (
            f"Invalid image digest format: {digest}. Expected sha256:..."
        )
