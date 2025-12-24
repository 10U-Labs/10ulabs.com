"""Tests for entrypoint configuration."""
from unittest.mock import patch
from test_helpers import run_entrypoint_and_get_config_args


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'test/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_url_format(mock_run, mock_popen):
    """Test that config.sh is called with correct URL format."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[2] == 'https://github.com/test/repo'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'my-token'
])
def test_config_sh_called_with_correct_token_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct token parameter."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[4] == 'my-token'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'my-runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_name_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct name parameter."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[6] == 'my-runner'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'my-labels', '--token', 'tok'
])
def test_config_sh_called_with_correct_labels_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct labels parameter."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[8] == 'my-labels'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_work_parameter(mock_run, mock_popen):
    """Test that config.sh is called with work parameter."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[10] == '_work'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_unattended_flag(mock_run, mock_popen):
    """Test that config.sh is called with unattended flag."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[11] == '--unattended'
