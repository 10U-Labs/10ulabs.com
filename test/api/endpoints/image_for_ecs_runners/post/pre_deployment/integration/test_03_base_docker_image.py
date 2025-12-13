"""Tests to validate base Docker image is pullable from Docker Hub.

Five-layer testing model:
- Layer 3: Existence - Does the base image exist on Docker Hub?
- Layer 4: Configuration - Does the image support arm64 architecture?

These tests verify that external dependencies this workflow needs exist.
"""

import pytest
import requests


BASE_IMAGE = "debian"
BASE_TAG = "stable-slim"


class TestBaseDockerImage:
    """Layer 3-4: Verify base Docker image exists and is properly configured."""

    def test_base_image_exists_on_docker_hub(self):
        """Verify the base Docker image exists on Docker Hub."""
        url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
        response = requests.get(url, timeout=30)
        assert response.status_code == 200, (
            f"Base image {BASE_IMAGE}:{BASE_TAG} not found on Docker Hub. "
            f"Status: {response.status_code}. "
            "Check that the image name and tag are correct."
        )

    def test_base_image_tag_matches(self):
        """Verify the Docker Hub API returns the correct tag."""
        url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            pytest.skip("Base image not found")
        data = response.json()
        assert data.get("name") == BASE_TAG, (
            f"Tag mismatch: expected {BASE_TAG}, got {data.get('name')}"
        )

    def test_base_image_supports_arm64(self):
        """Verify the base Docker image supports arm64 architecture."""
        url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            pytest.skip("Base image not found")
        data = response.json()
        images = data.get("images", [])
        architectures = [img.get("architecture") for img in images]
        assert "arm64" in architectures, (
            f"Base image {BASE_IMAGE}:{BASE_TAG} does not support arm64 architecture. "
            f"Available architectures: {architectures}. "
            "ECS runners require arm64 architecture."
        )
