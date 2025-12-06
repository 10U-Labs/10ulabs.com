"""Tests for promote_docker_image get_manifest functionality."""
import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_get_manifest_calls_describe_images():
    """Test that get_manifest calls describe_images."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert mock_client.describe_images.called


def test_get_manifest_returns_none_when_no_images():
    """Test that get_manifest returns None when no images found."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    result = promote_docker_image.get_image_manifest(
        mock_client, "repo", "tag"
    )
    assert result is None


def test_get_manifest_calls_batch_get_image_when_image_found():
    """Test that get_manifest calls batch_get_image when image found."""
    mock_client = Mock()
    image_details = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.describe_images.return_value = image_details
    mock_client.batch_get_image.return_value = {
        "images": [{"imageManifest": "{}"}]
    }
    promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert mock_client.batch_get_image.called


def test_get_manifest_returns_manifest_string():
    """Test that get_manifest returns manifest string."""
    mock_client = Mock()
    image_details = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.describe_images.return_value = image_details
    manifest = {"images": [{"imageManifest": "{\"test\":\"manifest\"}"}]}
    mock_client.batch_get_image.return_value = manifest
    result = promote_docker_image.get_image_manifest(
        mock_client, "repo", "tag"
    )
    assert result == "{\"test\":\"manifest\"}"


def test_get_manifest_returns_none_when_batch_get_returns_empty():
    """Test that get_manifest returns None when batch_get empty."""
    mock_client = Mock()
    image_details = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.describe_images.return_value = image_details
    mock_client.batch_get_image.return_value = {"images": []}
    result = promote_docker_image.get_image_manifest(
        mock_client, "repo", "tag"
    )
    assert result is None


def test_get_manifest_returns_none_on_client_error():
    """Test that get_manifest returns None on client error."""
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(
        error_response, "DescribeImages"
    )
    result = promote_docker_image.get_image_manifest(
        mock_client, "repo", "tag"
    )
    assert result is None


def test_get_manifest_passes_correct_repository_name():
    """Test that get_manifest passes correct repository name."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "my-repo", "tag")
    call_args = mock_client.describe_images.call_args[1]["repositoryName"]
    assert call_args == "my-repo"


def test_get_manifest_passes_correct_image_tag():
    """Test that get_manifest passes correct image tag."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "repo", "my-tag")
    call_args = mock_client.describe_images.call_args[1]["imageIds"][0]
    assert call_args["imageTag"] == "my-tag"
