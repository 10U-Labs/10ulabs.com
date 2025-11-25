import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_remove_tag_calls_describe_images():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert mock_client.describe_images.called


def test_remove_tag_returns_zero_when_image_found():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    result = promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert result == 0


def test_remove_tag_calls_batch_delete_when_image_exists():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert mock_client.batch_delete_image.called


def test_remove_tag_returns_zero_when_no_image_found():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    result = promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert result == 0


def test_remove_tag_returns_zero_on_image_not_found_exception():
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(error_response, "DescribeImages")
    result = promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert result == 0


def test_remove_tag_returns_one_on_other_client_error():
    mock_client = Mock()
    error_response = {"Error": {"Code": "RepositoryNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(error_response, "DescribeImages")
    result = promote_docker_image.remove_tag_from_image(mock_client, "repo", "tag", "us-east-1")
    assert result == 1


def test_remove_tag_passes_correct_repository_name():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "my-repo", "tag", "us-east-1")
    assert mock_client.describe_images.call_args[1]["repositoryName"] == "my-repo"


def test_remove_tag_passes_correct_image_tag():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.remove_tag_from_image(mock_client, "repo", "my-tag", "us-east-1")
    assert mock_client.describe_images.call_args[1]["imageIds"][0]["imageTag"] == "my-tag"
