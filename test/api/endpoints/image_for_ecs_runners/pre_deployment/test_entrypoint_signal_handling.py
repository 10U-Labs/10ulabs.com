"""Tests for entrypoint signal handling."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_sigterm_signal_registered(mock_run, mock_signal):
    """Test that SIGTERM signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[0][0][0] == entrypoint.signal.SIGTERM


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_sigint_signal_registered(mock_run, mock_signal):
    """Test that SIGINT signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[1][0][0] == entrypoint.signal.SIGINT


@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_exits_with_code_zero(mock_run):
    """Test that signal handler exits with code zero."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 0


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_function_registered(mock_run, mock_signal):
    """Test that signal handler function is registered."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert callable(mock_signal.call_args_list[0][0][1])


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_invokes_cleanup_runner(mock_run, mock_signal):
    """Test that signal handler invokes cleanup_runner."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    signal_handler = mock_signal.call_args_list[0][0][1]
    initial_call_count = mock_run.call_count
    with pytest.raises(SystemExit):
        signal_handler(None, None)
    assert mock_run.call_count > initial_call_count


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_calls_config_sh_remove(mock_run, mock_signal):
    """Test that signal handler calls config.sh remove."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    signal_handler = mock_signal.call_args_list[0][0][1]
    initial_call_count = mock_run.call_count
    with pytest.raises(SystemExit):
        signal_handler(None, None)
    config_remove_calls = [
        c for c in mock_run.call_args_list[initial_call_count:]
        if './config.sh' in c[0][0] and 'remove' in c[0][0]
    ]
    assert len(config_remove_calls) == 1


@patch('entrypoint.cleanup_runner')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_passes_registration_token_to_cleanup(
    mock_run, mock_cleanup
):
    """Test that signal handler passes registration token to cleanup."""
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_cleanup.call_args is None
