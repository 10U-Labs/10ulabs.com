"""Tests to validate base Docker image is pullable from Docker Hub."""
import requests


BASE_IMAGE = "debian"
BASE_TAG = "stable-slim"


def test_base_docker_image_exists_on_docker_hub():
    """Verify the base Docker image exists and is accessible on Docker Hub.

    This test uses the Docker Hub API to check that the image tag exists
    without requiring Docker to be installed.
    """
    # Docker Hub API for official images uses 'library' namespace
    url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
    response = requests.get(url, timeout=30)
    assert response.status_code == 200, (
        f"Base image {BASE_IMAGE}:{BASE_TAG} not found on Docker Hub. "
        f"Status: {response.status_code}"
    )
    data = response.json()
    assert data.get("name") == BASE_TAG, (
        f"Tag mismatch: expected {BASE_TAG}, got {data.get('name')}"
    )


def test_base_docker_image_has_amd64_architecture():
    """Verify the base Docker image has an amd64 architecture variant.

    ECS runners typically use amd64 architecture, so we need to ensure
    the image supports it.
    """
    url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
    response = requests.get(url, timeout=30)
    assert response.status_code == 200
    data = response.json()

    # Check that images array exists and contains amd64
    images = data.get("images", [])
    architectures = [img.get("architecture") for img in images]
    assert "amd64" in architectures, (
        f"Base image {BASE_IMAGE}:{BASE_TAG} does not support amd64 architecture. "
        f"Available architectures: {architectures}"
    )
