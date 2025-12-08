"""Tests for promote_docker_image remove_tag functionality."""
import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_remove_tag_calls_describe_images():
    """Test that remove_tag calls describe_images."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag")
    assert mock_client.describe_images.called


def test_remove_tag_returns_zero_when_image_found():
    """Test that remove_tag returns zero when image is found."""
    mock_client = Mock()
    image_details = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.describe_images.return_value = image_details
    result = promote_docker_image.remove_tag_from_image(
        mock_client, "repo", "tag"
    )
    assert result == 0


def test_remove_tag_calls_batch_delete_when_image_exists():
    """Test that remove_tag calls batch_delete when image exists."""
    mock_client = Mock()
    image_details = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.describe_images.return_value = image_details
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag")
    assert mock_client.batch_delete_image.called


def test_remove_tag_returns_zero_when_no_image_found():
    """Test that remove_tag returns zero when no image is found."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    result = promote_docker_image.remove_tag_from_image(
        mock_client, "repo", "tag"
    )
    assert result == 0


def test_remove_tag_returns_zero_on_image_not_found_exception():
    """Test that remove_tag returns zero on ImageNotFoundException."""
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(
        error_response, "DescribeImages"
    )
    result = promote_docker_image.remove_tag_from_image(
        mock_client, "repo", "tag"
    )
    assert result == 0


def test_remove_tag_returns_one_on_other_client_error():
    """Test that remove_tag returns one on other client errors."""
    mock_client = Mock()
    error_response = {"Error": {"Code": "RepositoryNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(
        error_response, "DescribeImages"
    )
    result = promote_docker_image.remove_tag_from_image(
        mock_client, "repo", "tag"
    )
    assert result == 1


def test_remove_tag_passes_correct_repository_name():
    """Test that remove_tag passes correct repository name."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "my-repo", "tag")
    call_args = mock_client.describe_images.call_args[1]["repositoryName"]
    assert call_args == "my-repo"


def test_remove_tag_passes_correct_image_tag():
    """Test that remove_tag passes correct image tag."""
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "my-tag")
    call_args = mock_client.describe_images.call_args[1]["imageIds"][0]
    assert call_args["imageTag"] == "my-tag"
