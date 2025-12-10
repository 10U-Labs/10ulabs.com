"""Tests for ECR image in ECS runner deployment."""
import subprocess
import boto3
from ..conftest import login_to_ecr


def test_ecr_image_exists(aws_region, ecr_repository, image_tag):
    """Test that ECR image exists with expected tag."""
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert len(response["imageDetails"]) == 1


def test_ecr_image_is_arm64(aws_region, ecr_repository, image_tag):
    """Test that ECR image is ARM64 multi-platform."""
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    expected_media_type = "application/vnd.oci.image.index.v1+json"
    assert (
        response["imageDetails"][0]["imageManifestMediaType"]
        == expected_media_type
    )


def test_ecr_image_can_be_pulled(ecr_image_uri, aws_region):
    """Test that ECR image can be pulled."""
    login_to_ecr(aws_region)

    result = subprocess.run(
        ["docker", "pull", "--platform", "linux/arm64", ecr_image_uri],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
