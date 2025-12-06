"""Tests for entrypoint configuration."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'test/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_url_format(mock_run):
    """Test that config.sh is called with correct URL format."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][2] == 'https://github.com/test/repo'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'my-token'
])
def test_config_sh_called_with_correct_token_parameter(mock_run):
    """Test that config.sh is called with correct token parameter."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][4] == 'my-token'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'my-runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_name_parameter(mock_run):
    """Test that config.sh is called with correct name parameter."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][6] == 'my-runner'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'my-labels', '--token', 'tok'
])
def test_config_sh_called_with_correct_labels_parameter(mock_run):
    """Test that config.sh is called with correct labels parameter."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][8] == 'my-labels'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_work_parameter(mock_run):
    """Test that config.sh is called with work parameter."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][10] == '_work'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_unattended_flag(mock_run):
    """Test that config.sh is called with unattended flag."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][11] == '--unattended'
