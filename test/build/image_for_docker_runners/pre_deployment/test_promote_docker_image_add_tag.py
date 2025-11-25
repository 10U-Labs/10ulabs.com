import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_add_tag_calls_put_image():
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "repo", "{}", "tag", "us-east-1")
    assert mock_client.put_image.called


def test_add_tag_returns_zero_on_success():
    mock_client = Mock()
    result = promote_docker_image.add_tag_to_image(mock_client, "repo", "{}", "tag", "us-east-1")
    assert result == 0


def test_add_tag_returns_one_on_client_error():
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageAlreadyExistsException"}}
    mock_client.put_image.side_effect = ClientError(error_response, "PutImage")
    result = promote_docker_image.add_tag_to_image(mock_client, "repo", "{}", "tag", "us-east-1")
    assert result == 1


def test_add_tag_passes_correct_repository_name():
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "my-repo", "{}", "tag", "us-east-1")
    assert mock_client.put_image.call_args[1]["repositoryName"] == "my-repo"


def test_add_tag_passes_correct_image_tag():
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "repo", "{}", "my-tag", "us-east-1")
    assert mock_client.put_image.call_args[1]["imageTag"] == "my-tag"


def test_add_tag_passes_correct_manifest():
    mock_client = Mock()
    promote_docker_image.add_tag_to_image(mock_client, "repo", "{\"test\":true}", "tag", "us-east-1")
    assert mock_client.put_image.call_args[1]["imageManifest"] == "{\"test\":true}"
