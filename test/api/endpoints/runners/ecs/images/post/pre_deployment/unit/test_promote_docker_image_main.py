"""Tests for promote_docker_image main function."""
import sys
from unittest.mock import patch

promote_docker_image = sys.modules['promote_docker_image']


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'my-repo',
    '--image-tag', 'v1.0', '--region', 'us-east-1'
])
def test_main_calls_promote_image(mock_promote):
    """Test that main calls promote_image."""
    mock_promote.return_value = 0
    try:
        promote_docker_image.main()
    except SystemExit:
        pass
    assert mock_promote.called


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'my-repo',
    '--image-tag', 'v1.0', '--region', 'us-east-1'
])
def test_main_passes_repository_to_promote_image(mock_promote):
    """Test that main passes repository to promote_image."""
    mock_promote.return_value = 0
    try:
        promote_docker_image.main()
    except SystemExit:
        pass
    assert mock_promote.call_args[0][0] == "my-repo"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'repo',
    '--image-tag', 'v2.0', '--region', 'us-east-1'
])
def test_main_passes_image_tag_to_promote_image(mock_promote):
    """Test that main passes image tag to promote_image."""
    mock_promote.return_value = 0
    try:
        promote_docker_image.main()
    except SystemExit:
        pass
    assert mock_promote.call_args[0][1] == "v2.0"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'repo',
    '--image-tag', 'v1.0', '--region', 'eu-west-1'
])
def test_main_passes_region_to_promote_image(mock_promote):
    """Test that main passes region to promote_image."""
    mock_promote.return_value = 0
    try:
        promote_docker_image.main()
    except SystemExit:
        pass
    assert mock_promote.call_args[0][2] == "eu-west-1"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'repo',
    '--image-tag', 'v1.0', '--region', 'us-east-1'
])
def test_main_exits_with_promote_image_result(mock_promote):
    """Test that main exits with promote_image result."""
    mock_promote.return_value = 42
    try:
        promote_docker_image.main()
    except SystemExit as e:
        assert e.code == 42


@patch('promote_docker_image.promote_image')
@patch('sys.argv', [
    'promote_docker_image.py', '--repository', 'repo',
    '--image-tag', 'v1.0', '--region', 'us-east-1'
])
def test_main_exits_with_zero_on_success(mock_promote):
    """Test that main exits with zero on success."""
    mock_promote.return_value = 0
    try:
        promote_docker_image.main()
    except SystemExit as e:
        assert e.code == 0
