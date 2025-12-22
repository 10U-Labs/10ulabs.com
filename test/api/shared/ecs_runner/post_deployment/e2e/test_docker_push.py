"""E2E tests for ECR Docker push/pull functionality.

User Journey: Docker client pushes and pulls images to/from ECR

When: A Docker client authenticates and pushes an image to ECR
Then: The image is stored and can be verified in the repository

Critical Path: Docker login → Build image → Push to ECR → Verify exists
Failure Impact: ECS runner images cannot be pushed, breaking runner deployments
"""


def test_pushed_image_exists_in_ecr(ecr_client, pushed_test_image):
    """Verify pushed image appears in ECR repository."""
    images = ecr_client.describe_images(
        repositoryName=pushed_test_image["repository"],
        imageIds=[{"imageTag": pushed_test_image["tag"]}]
    )
    assert len(images["imageDetails"]) == 1
