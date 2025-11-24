import os
import subprocess
import boto3
import pytest


def get_dockerfile_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/build/image_for_docker_runners/Dockerfile")


def get_docker_image_tag():
    return os.environ.get("TEST_DOCKER_IMAGE_TAG", "github-docker-runner:test")


@pytest.fixture(scope="module")
def dockerfile_path():
    return get_dockerfile_path()


@pytest.fixture(scope="module")
def docker_image_tag():
    return get_docker_image_tag()


@pytest.fixture(scope="module")
def docker_image():
    path = get_dockerfile_path()
    tag = get_docker_image_tag()
    build_context = os.path.dirname(path)

    result = subprocess.run(
        ["docker", "build", "--platform", "linux/arm64", "-t", tag, "-f", path, build_context],
        check=False,
        capture_output=True,
        text=True,
        errors='replace'
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed: {result.stderr}")

    yield tag

    subprocess.run(["docker", "rmi", "-f", tag], check=False, capture_output=True)


def get_available_ecr_tag(region, repository):
    client = boto3.client("ecr", region_name=region)
    response = client.describe_images(
        repositoryName=repository,
        imageIds=[{"imageTag": "available"}]
    )
    tags = response["imageDetails"][0].get("imageTags", [])
    tag = next((t for t in tags if t == "available"), None)
    if not tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return tag


@pytest.fixture(scope="module")
def image_tag(aws_region, ecr_repository):
    return get_available_ecr_tag(aws_region, ecr_repository)


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository):
    tag = get_available_ecr_tag(aws_region, ecr_repository)
    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:{tag}"


def login_to_ecr(region):
    password_result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True,
        capture_output=True,
        text=True
    )
    account_result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=True,
        capture_output=True,
        text=True
    )
    account_id = account_result.stdout.strip()
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin",
         f"{account_id}.dkr.ecr.{region}.amazonaws.com"],
        input=password_result.stdout,
        check=True,
        text=True
    )
