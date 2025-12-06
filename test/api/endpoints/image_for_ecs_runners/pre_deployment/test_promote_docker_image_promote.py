"""Tests for promote_docker_image promote functionality."""
import sys
from unittest.mock import patch

promote_docker_image = sys.modules['promote_docker_image']


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_calls_remove_tag_first(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image calls remove_tag first."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_remove.called


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_early_when_remove_fails(
    mock_remove, _mock_get, _mock_add, _mock_boto
):
    """Test that promote_image returns early when remove fails."""
    mock_remove.return_value = 1
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_calls_get_manifest(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image calls get_manifest."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_get.called


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_one_when_manifest_not_found(
    mock_remove, mock_get, _mock_add, _mock_boto
):
    """Test that promote_image returns one when manifest not found."""
    mock_remove.return_value = 0
    mock_get.return_value = None
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_adds_latest_tag(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image adds latest tag."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_add.call_args_list[0][0][3] == "latest"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_adds_stable_tag(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image adds stable tag."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_add.call_args_list[1][0][3] == "stable"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_removes_available_tag(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image removes available tag."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_remove.call_args_list[1][0][2] == "available"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_zero_on_success(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image returns zero on success."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 0


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_early_when_add_latest_fails(
    mock_remove, mock_get, mock_add, _mock_boto
):
    """Test that promote_image returns early when add latest fails."""
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.side_effect = [1]
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1
