"""Shared test data factories for runners/ecs/images endpoint tests."""
from datetime import datetime, timezone

IMAGE_RESPONSE_FIELDS = ('digest', 'tags', 'pushed_at', 'size_bytes', 'repository')


def make_ecr_image_detail(
    digest="sha256:abc123",
    tags=None,
    pushed_at=None,
    size_bytes=1024
):
    """Create a mock ECR image detail dict.

    Args:
        digest: Image digest string
        tags: List of tags, defaults to ['v1.0']
        pushed_at: Datetime for pushed time, defaults to 2024-01-01
        size_bytes: Image size in bytes

    Returns:
        dict matching ECR describe_images response format
    """
    if tags is None:
        tags = ['v1.0']
    if pushed_at is None:
        pushed_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return {
        'imageDigest': digest,
        'imageTags': tags,
        'imagePushedAt': pushed_at,
        'imageSizeInBytes': size_bytes
    }


def make_ecr_describe_response(images=None):
    """Create a mock ECR describe_images response.

    Args:
        images: List of image detail dicts, or None for empty response

    Returns:
        dict matching ECR describe_images API response format
    """
    if images is None:
        images = []
    return {'imageDetails': images}


def make_stable_image(digest="sha256:stable123", additional_tags=None):
    """Create a mock stable ECR image.

    Args:
        digest: Image digest string
        additional_tags: Additional tags besides 'stable'

    Returns:
        dict matching ECR describe_images response format for a stable image
    """
    tags = ['stable']
    if additional_tags:
        tags.extend(additional_tags)
    return make_ecr_image_detail(digest=digest, tags=tags)
