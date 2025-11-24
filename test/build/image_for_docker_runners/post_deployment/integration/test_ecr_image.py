import subprocess
import boto3
from ..conftest import login_to_ecr


def test_ecr_image_exists(aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert len(response["imageDetails"]) == 1


def test_ecr_image_is_arm64(aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert response["imageDetails"][0]["imageManifestMediaType"] == "application/vnd.oci.image.index.v1+json"


def test_ecr_image_can_be_pulled(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        ["docker", "pull", "--platform", "linux/arm64", ecr_image_uri],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
