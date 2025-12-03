import sys
from unittest.mock import patch

import pytest

promote_docker_image = sys.modules['promote_docker_image']


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'my-repo', '--image-tag', 'v1.0', '--region', 'us-east-1'])
def test_main_calls_promote_image(mock_promote):
    mock_promote.return_value = 0
    with pytest.raises(SystemExit):
        promote_docker_image.main()
    assert mock_promote.called


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'my-repo', '--image-tag', 'v1.0', '--region', 'us-east-1'])
def test_main_passes_repository_to_promote_image(mock_promote):
    mock_promote.return_value = 0
    with pytest.raises(SystemExit):
        promote_docker_image.main()
    assert mock_promote.call_args[0][0] == "my-repo"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'repo', '--image-tag', 'v2.0', '--region', 'us-east-1'])
def test_main_passes_image_tag_to_promote_image(mock_promote):
    mock_promote.return_value = 0
    with pytest.raises(SystemExit):
        promote_docker_image.main()
    assert mock_promote.call_args[0][1] == "v2.0"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'repo', '--image-tag', 'v1.0', '--region', 'eu-west-1'])
def test_main_passes_region_to_promote_image(mock_promote):
    mock_promote.return_value = 0
    with pytest.raises(SystemExit):
        promote_docker_image.main()
    assert mock_promote.call_args[0][2] == "eu-west-1"


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'repo', '--image-tag', 'v1.0', '--region', 'us-east-1'])
def test_main_exits_with_promote_image_result(mock_promote):
    mock_promote.return_value = 42
    with pytest.raises(SystemExit) as exc_info:
        promote_docker_image.main()
    assert exc_info.value.code == 42


@patch('promote_docker_image.promote_image')
@patch('sys.argv', ['promote_docker_image.py', '--repository', 'repo', '--image-tag', 'v1.0', '--region', 'us-east-1'])
def test_main_exits_with_zero_on_success(mock_promote):
    mock_promote.return_value = 0
    with pytest.raises(SystemExit) as exc_info:
        promote_docker_image.main()
    assert exc_info.value.code == 0
