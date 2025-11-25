from unittest.mock import Mock, patch
import importlib.util
import os
import sys


BASE_DIR = os.path.join(os.path.dirname(__file__), '../../../../src/build/image_for_docker_runners')
sys.path.insert(0, BASE_DIR)
promote_path = os.path.join(BASE_DIR, 'promote_docker_image.py')
promote_spec = importlib.util.spec_from_file_location("promote_docker_image", promote_path)
if promote_spec is None or promote_spec.loader is None:
    raise ImportError("Could not load promote_docker_image module")
promote_docker_image = importlib.util.module_from_spec(promote_spec)
promote_spec.loader.exec_module(promote_docker_image)


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_calls_remove_tag_first(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_remove.called


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_early_when_remove_fails(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 1
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_calls_get_manifest(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_get.called


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_one_when_manifest_not_found(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = None
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_adds_latest_tag(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_add.call_args_list[0][0][3] == "latest"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_adds_stable_tag(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_add.call_args_list[1][0][3] == "stable"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_removes_available_tag(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert mock_remove.call_args_list[1][0][2] == "available"


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_zero_on_success(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.return_value = 0
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 0


@patch('promote_docker_image.boto3')
@patch('promote_docker_image.add_tag_to_image')
@patch('promote_docker_image.get_image_manifest')
@patch('promote_docker_image.remove_tag_from_image')
def test_promote_image_returns_early_when_add_latest_fails(mock_remove, mock_get, mock_add, mock_boto):
    mock_remove.return_value = 0
    mock_get.return_value = "{}"
    mock_add.side_effect = [1]
    result = promote_docker_image.promote_image("repo", "tag", "us-east-1")
    assert result == 1
