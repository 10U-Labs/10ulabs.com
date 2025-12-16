"""Tests for entrypoint signal handling."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


def setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for signal handling tests - validates SIGTERM/SIGINT."""
    signal_process = Mock()
    signal_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=signal_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return signal_process


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_sigterm_signal_registered(mock_run, mock_signal, mock_popen):
    """Test that SIGTERM signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[0][0][0] == entrypoint.signal.SIGTERM


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_sigint_signal_registered(mock_run, mock_signal, mock_popen):
    """Test that SIGINT signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[1][0][0] == entrypoint.signal.SIGINT


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_exits_with_code_zero(mock_run, mock_popen):
    """Test that signal handler exits with code zero."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 0


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_function_registered(mock_run, mock_signal, mock_popen):
    """Test that signal handler function is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert callable(mock_signal.call_args_list[0][0][1])


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_invokes_cleanup_runner(mock_run, mock_signal, mock_popen):
    """Test that signal handler invokes cleanup_runner."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    signal_handler = mock_signal.call_args_list[0][0][1]
    initial_call_count = mock_run.call_count
    with pytest.raises(SystemExit):
        signal_handler(None, None)
    assert mock_run.call_count > initial_call_count


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.stop_cloudwatch_agent')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_stops_cloudwatch_agent(
    mock_run, mock_signal, mock_stop, mock_popen
):
    """Test that signal handler stops CloudWatch agent."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    signal_handler = mock_signal.call_args_list[0][0][1]
    mock_stop.reset_mock()
    with pytest.raises(SystemExit):
        signal_handler(None, None)
    mock_stop.assert_called_once()
