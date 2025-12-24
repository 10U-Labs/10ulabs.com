"""Tests for entrypoint configuration."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


def _setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for configuration tests - verifies config.sh params."""
    config_process = Mock()
    config_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=config_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return config_process


def _find_config_sh_call(mock_run):
    """Find the config.sh call in the mock call list.

    The first two calls are permission-fix calls (mkdir, chown), config.sh is third.
    """
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and args[0] == './config.sh':
            return args
    return None


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'test/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_url_format(mock_run, mock_popen):
    """Test that config.sh is called with correct URL format."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[2] == 'https://github.com/test/repo'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'my-token'
])
def test_config_sh_called_with_correct_token_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct token parameter."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[4] == 'my-token'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'my-runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_correct_name_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct name parameter."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[6] == 'my-runner'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'my-labels', '--token', 'tok'
])
def test_config_sh_called_with_correct_labels_parameter(mock_run, mock_popen):
    """Test that config.sh is called with correct labels parameter."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[8] == 'my-labels'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_work_parameter(mock_run, mock_popen):
    """Test that config.sh is called with work parameter."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[10] == '_work'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_config_sh_called_with_unattended_flag(mock_run, mock_popen):
    """Test that config.sh is called with unattended flag."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[11] == '--unattended'
