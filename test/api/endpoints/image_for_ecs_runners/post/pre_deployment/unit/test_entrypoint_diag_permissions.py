"""Tests for entrypoint _diag folder permission handling.

Tests verify that the entrypoint properly sets up _diag folder permissions
before configuring the runner, enabling CloudWatch sidecar to read logs.
"""
from unittest.mock import Mock, patch
import pytest
import entrypoint


def _setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for tests."""
    popen_process = Mock()
    popen_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=popen_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return popen_process


def _find_mkdir_call(mock_run):
    """Find the mkdir call for _diag directory."""
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and 'mkdir' in args and '/home/runner/_diag' in args:
            return args
    return None


def _find_chown_call(mock_run):
    """Find the chown call for _diag directory."""
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and 'chown' in args and '/home/runner/_diag' in args:
            return args
    return None


def _get_call_indices(mock_run):
    """Get indices of mkdir and chown calls for _diag directory."""
    mkdir_index = None
    chown_index = None
    for i, call in enumerate(mock_run.call_args_list):
        args = call[0][0] if call[0] else []
        if args and 'mkdir' in args and '/home/runner/_diag' in args:
            mkdir_index = i
        if args and 'chown' in args and '/home/runner/_diag' in args:
            chown_index = i
    return mkdir_index, chown_index


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_calls_sudo_mkdir_for_diag(mock_run, mock_popen):
    """Test that main calls sudo mkdir for _diag directory."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()

    mkdir_args = _find_mkdir_call(mock_run)
    assert mkdir_args is not None and mkdir_args[0] == 'sudo' and mkdir_args[1] == 'mkdir'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_calls_sudo_chown_for_diag(mock_run, mock_popen):
    """Test that main calls sudo chown for _diag directory."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()

    chown_args = _find_chown_call(mock_run)
    assert chown_args is not None and chown_args[0] == 'sudo' and chown_args[1] == 'chown'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_calls_mkdir_before_chown(mock_run, mock_popen):
    """Test that mkdir is called before chown for _diag directory."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()

    mkdir_index, chown_index = _get_call_indices(mock_run)
    assert mkdir_index is not None and chown_index is not None and mkdir_index < chown_index


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_continues_if_permission_fix_fails(mock_run, mock_popen):
    """Test that main continues even if permission fix commands fail."""
    mock_run.side_effect = [
        Mock(returncode=1),  # mkdir fails
        Mock(returncode=1),  # chown fails
        Mock(returncode=0),  # config.sh succeeds
    ]
    _setup_popen_mock(mock_popen)

    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()

    assert exc_info.value.code == 0
