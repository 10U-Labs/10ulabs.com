import sys
from unittest.mock import Mock

from botocore.exceptions import ClientError

promote_docker_image = sys.modules['promote_docker_image']


def test_get_manifest_calls_describe_images():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert mock_client.describe_images.called


def test_get_manifest_returns_none_when_no_images():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    result = promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert result is None


def test_get_manifest_calls_batch_get_image_when_image_found():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.batch_get_image.return_value = {"images": [{"imageManifest": "{}"}]}
    promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert mock_client.batch_get_image.called


def test_get_manifest_returns_manifest_string():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.batch_get_image.return_value = {"images": [{"imageManifest": "{\"test\":\"manifest\"}"}]}
    result = promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert result == "{\"test\":\"manifest\"}"


def test_get_manifest_returns_none_when_batch_get_returns_empty():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": [{"imageDigest": "sha256:abc"}]}
    mock_client.batch_get_image.return_value = {"images": []}
    result = promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert result is None


def test_get_manifest_returns_none_on_client_error():
    mock_client = Mock()
    error_response = {"Error": {"Code": "ImageNotFoundException"}}
    mock_client.describe_images.side_effect = ClientError(error_response, "DescribeImages")
    result = promote_docker_image.get_image_manifest(mock_client, "repo", "tag")
    assert result is None


def test_get_manifest_passes_correct_repository_name():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "my-repo", "tag")
    assert mock_client.describe_images.call_args[1]["repositoryName"] == "my-repo"


def test_get_manifest_passes_correct_image_tag():
    mock_client = Mock()
    mock_client.describe_images.return_value = {"imageDetails": []}
    promote_docker_image.get_image_manifest(mock_client, "repo", "my-tag")
    assert mock_client.describe_images.call_args[1]["imageIds"][0]["imageTag"] == "my-tag"
