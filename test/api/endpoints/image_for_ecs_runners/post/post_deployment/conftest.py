"""Test fixtures for ECS runner image post-deployment tests."""
import json
import os
import subprocess

from test.api.endpoints.image_for_ecs_runners.conftest import CONFIG_PATH, DOCKERFILE_PATH

import boto3
import pytest


def _get_config_value(key):
    """Get a value from the image config.json."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get(key)


def get_dockerfile_path():
    """Get the path to the Dockerfile."""
    return DOCKERFILE_PATH


def get_docker_image_tag():
    """Get the Docker image tag from environment or config."""
    try:
        tag = os.environ["TEST_DOCKER_IMAGE_TAG"]
    except KeyError:
        container_name = _get_config_value("container_name")
        tag = f"{container_name}:test"
    return tag


@pytest.fixture(scope="module")
def dockerfile_path():
    """Fixture that provides the Dockerfile path."""
    return get_dockerfile_path()


@pytest.fixture(scope="module")
def docker_image_tag():
    """Fixture that provides the Docker image tag."""
    return get_docker_image_tag()


@pytest.fixture(scope="module")
def docker_image(aws_region, aws_account_id, ecr_repository):
    """Fixture that pulls ECR image and tags it for local testing."""
    tag = get_docker_image_tag()
    ecr_tag = get_available_ecr_tag(aws_region, ecr_repository)
    ecr_uri = (
        f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/"
        f"{ecr_repository}:{ecr_tag}"
    )

    login_to_ecr(aws_region)

    pull_result = subprocess.run(
        ["docker", "pull", "--platform", "linux/arm64", ecr_uri],
        check=False,
        capture_output=True,
        text=True,
        errors='replace'
    )

    if pull_result.returncode != 0:
        pytest.fail(f"Docker pull failed: {pull_result.stderr}")

    tag_result = subprocess.run(
        ["docker", "tag", ecr_uri, tag],
        check=False,
        capture_output=True,
        text=True,
        errors='replace'
    )

    if tag_result.returncode != 0:
        pytest.fail(f"Docker tag failed: {tag_result.stderr}")

    yield tag

    subprocess.run(
        ["docker", "rmi", "-f", tag],
        check=False,
        capture_output=True
    )


def get_available_ecr_tag(region, repository):
    """Get the 'available' tag from ECR repository."""
    client = boto3.client("ecr", region_name=region)
    response = client.describe_images(
        repositoryName=repository,
        imageIds=[{"imageTag": "available"}]
    )
    try:
        tags = response["imageDetails"][0]["imageTags"]
    except KeyError:
        tags = []
    tag = None
    index = 0
    while index < len(tags):
        if tags[index] == "available":
            tag = tags[index]
            break
        index = index + 1
    if not tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return tag


@pytest.fixture(scope="module")
def image_tag(aws_region, ecr_repository):
    """Fixture that provides the ECR image tag."""
    return get_available_ecr_tag(aws_region, ecr_repository)


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository):
    """Fixture that provides the full ECR image URI."""
    tag = get_available_ecr_tag(aws_region, ecr_repository)
    return (
        f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/"
        f"{ecr_repository}:{tag}"
    )


def login_to_ecr(region):
    """Authenticate Docker with ECR."""
    password_result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True,
        capture_output=True,
        text=True
    )
    account_result = subprocess.run(
        [
            "aws", "sts", "get-caller-identity",
            "--query", "Account",
            "--output", "text"
        ],
        check=True,
        capture_output=True,
        text=True
    )
    account_id = account_result.stdout.strip()
    subprocess.run(
        [
            "docker", "login",
            "--username", "AWS",
            "--password-stdin",
            f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        ],
        input=password_result.stdout,
        check=True,
        text=True
    )


def run_github_api_curl(args):
    """Run a curl command and return parsed JSON response."""
    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)


def get_runner_registration_token(pat, repo):
    """Generate a GitHub Actions runner registration token."""
    response = run_github_api_curl([
        "curl",
        "-X", "POST",
        "-H", f"Authorization: token {pat}",
        "-H", "Accept: application/vnd.github.v3+json",
        f"https://api.github.com/repos/{repo}/actions/runners/registration-token"
    ])
    try:
        token = response["token"]
    except KeyError:
        token = ""
    return token


@pytest.fixture(scope="module")
def runner_registration_token(github_pat, github_repo):
    """Fixture that generates a GitHub Actions runner registration token."""
    return get_runner_registration_token(github_pat, github_repo)
