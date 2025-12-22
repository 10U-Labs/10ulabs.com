"""Pytest fixtures for api/shared/ecs_runner e2e tests.

Shared fixtures (expected_ecr_name, aws clients) provided by parent conftest.py.
"""

import base64
import subprocess
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator

import pytest


@dataclass
class ImageBuildConfig:
    """Configuration for building and pushing a Docker image."""

    ecr_client: Any
    registry_url: str
    repo_name: str
    tag_prefix: str
    dockerfile_content: bytes
    build_timeout: int


@pytest.fixture(scope="module")
def ecr_registry_url(shared_config):
    """Get the ECR registry URL."""
    account_id = shared_config["aws_account_id"]
    region = shared_config["aws_region"]
    return f"{account_id}.dkr.ecr.{region}.amazonaws.com"


@pytest.fixture(scope="module")
def docker_logged_in(ecr_client, shared_config):
    """Ensure Docker is logged into ECR."""
    auth = ecr_client.get_authorization_token()
    token = auth["authorizationData"][0]["authorizationToken"]

    account_id = shared_config["aws_account_id"]
    region = shared_config["aws_region"]
    registry_url = f"{account_id}.dkr.ecr.{region}.amazonaws.com"

    login_cmd = [
        "docker", "login",
        "--username", "AWS",
        "--password-stdin",
        registry_url
    ]

    decoded = base64.b64decode(token).decode("utf-8")
    password = decoded.split(":")[1]

    result = subprocess.run(
        login_cmd,
        input=password.encode(),
        capture_output=True,
        timeout=30,
        check=False
    )

    if result.returncode != 0:
        pytest.skip(f"Docker login failed: {result.stderr.decode()}")

    return True


@contextmanager
def build_push_cleanup_image(
    config: ImageBuildConfig
) -> Generator[dict[str, str], None, None]:
    """Build, push, yield image info, then cleanup."""
    test_tag = f"{config.tag_prefix}-{uuid.uuid4().hex[:8]}"
    full_image = f"{config.registry_url}/{config.repo_name}:{test_tag}"

    subprocess.run(
        ["docker", "build", "-t", full_image, "-f", "-", "."],
        input=config.dockerfile_content,
        capture_output=True,
        timeout=config.build_timeout,
        cwd="/tmp",
        check=True
    )

    subprocess.run(
        ["docker", "push", full_image],
        capture_output=True,
        timeout=120,
        check=True
    )

    try:
        yield {"tag": test_tag, "full_image": full_image, "repository": config.repo_name}
    finally:
        subprocess.run(
            ["docker", "rmi", full_image],
            capture_output=True,
            timeout=30,
            check=False
        )
        try:
            config.ecr_client.batch_delete_image(
                repositoryName=config.repo_name,
                imageIds=[{"imageTag": test_tag}]
            )
        except (config.ecr_client.exceptions.ImageNotFoundException, KeyError):
            pass


@pytest.fixture(scope="module")
def pushed_test_image(request, ecr_client, expected_ecr_name):
    """Build and push a test image, clean up after tests."""
    request.getfixturevalue("docker_logged_in")
    registry_url = request.getfixturevalue("ecr_registry_url")

    config = ImageBuildConfig(
        ecr_client=ecr_client,
        registry_url=registry_url,
        repo_name=expected_ecr_name,
        tag_prefix="e2e-test",
        dockerfile_content=b"FROM debian:stable-slim\nLABEL test=e2e\n",
        build_timeout=60
    )
    with build_push_cleanup_image(config) as image_info:
        yield image_info


@pytest.fixture(scope="module")
def pushed_scannable_image(request, ecr_client, expected_ecr_name):
    """Build and push an image that can be scanned, clean up after tests."""
    request.getfixturevalue("docker_logged_in")
    registry_url = request.getfixturevalue("ecr_registry_url")

    config = ImageBuildConfig(
        ecr_client=ecr_client,
        registry_url=registry_url,
        repo_name=expected_ecr_name,
        tag_prefix="e2e-scan-test",
        dockerfile_content=b"FROM debian:stable-slim\nLABEL test=e2e-scan\n",
        build_timeout=120
    )
    with build_push_cleanup_image(config) as image_info:
        yield image_info
