"""Tests to validate ECR has a stable image for ECS runners."""


def test_ecr_repository_exists(ecr_client, api_shared_ecr_outputs):
    """Verify the ECR repository exists and is accessible."""
    repository_name = api_shared_ecr_outputs.get("repository_name")
    assert repository_name, "repository_name output not found"

    response = ecr_client.describe_repositories(
        repositoryNames=[repository_name]
    )
    assert len(response["repositories"]) == 1
    repo = response["repositories"][0]
    assert repo["repositoryName"] == repository_name


def test_ecr_has_stable_image(ecr_client, api_shared_ecr_outputs):
    """Verify at least one image with 'stable' tag exists in ECR."""
    repository_name = api_shared_ecr_outputs.get("repository_name")
    assert repository_name, "repository_name output not found"

    response = ecr_client.describe_images(
        repositoryName=repository_name,
        imageIds=[{"imageTag": "stable"}]
    )
    assert len(response["imageDetails"]) >= 1, \
        "No stable image found in ECR repository"


def test_stable_image_is_available(ecr_client, api_shared_ecr_outputs):
    """Verify the stable image has a valid digest."""
    repository_name = api_shared_ecr_outputs.get("repository_name")
    assert repository_name, "repository_name output not found"

    response = ecr_client.describe_images(
        repositoryName=repository_name,
        imageIds=[{"imageTag": "stable"}]
    )
    assert len(response["imageDetails"]) >= 1
    image = response["imageDetails"][0]
    assert "imageDigest" in image, "Stable image missing digest"
    assert image["imageDigest"].startswith("sha256:"), \
        "Invalid image digest format"
