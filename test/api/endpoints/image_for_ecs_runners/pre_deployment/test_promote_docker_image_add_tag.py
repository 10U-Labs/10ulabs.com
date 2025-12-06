"""Tests for promote_docker_image add_tag functionality."""
import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_add_tag_calls_put_image():
    """Test that add_tag calls put_image."""
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "repo", "{}", "tag")
    assert mock_client.put_image.called


def test_add_tag_returns_zero_on_success():
    """Test that add_tag returns zero on success."""
    mock_client = Mock()
    result = promote_docker_image.add_tag_to_image(
        mock_client, "repo", "{}", "tag"
    )
    assert result == 0


def test_add_tag_returns_one_on_client_error():
    """Test that add_tag returns one on client error."""
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageAlreadyExistsException"}}
    mock_client.put_image.side_effect = ClientError(
        error_response, "PutImage"
    )
    result = promote_docker_image.add_tag_to_image(
        mock_client, "repo", "{}", "tag"
    )
    assert result == 1


def test_add_tag_passes_correct_repository_name():
    """Test that add_tag passes correct repository name."""
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "my-repo", "{}", "tag")
    assert mock_client.put_image.call_args[1]["repositoryName"] == "my-repo"


def test_add_tag_passes_correct_image_tag():
    """Test that add_tag passes correct image tag."""
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(
        mock_client, "repo", "{}", "my-tag"
    )
    assert mock_client.put_image.call_args[1]["imageTag"] == "my-tag"


def test_add_tag_passes_correct_manifest():
    """Test that add_tag passes correct manifest."""
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(
        mock_client, "repo", "{\"test\":true}", "tag"
    )
    call_args = mock_client.put_image.call_args[1]["imageManifest"]
    assert call_args == "{\"test\":true}"
