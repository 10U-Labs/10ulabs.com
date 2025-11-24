import os
import subprocess
import pytest
import boto3


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
