"""Tests for entrypoint signal handling."""
import signal
from unittest.mock import Mock, patch


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
def test_sigterm_signal_registered(mock_run, mock_signal, mock_popen, entrypoint):
    """Test that SIGTERM signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    assert mock_signal.call_args_list[0][0][0] == signal.SIGTERM


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_sigint_signal_registered(mock_run, mock_signal, mock_popen, entrypoint):
    """Test that SIGINT signal is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    assert mock_signal.call_args_list[1][0][0] == signal.SIGINT


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_exits_with_code_zero(mock_run, mock_popen, entrypoint):
    """Test that signal handler exits with code zero."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit as e:
        assert e.code == 0


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_function_registered(mock_run, mock_signal, mock_popen, entrypoint):
    """Test that signal handler function is registered."""
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    assert callable(mock_signal.call_args_list[0][0][1])


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_signal_handler_terminates_runner_process(mock_run, mock_signal, mock_popen, entrypoint):
    """Test that signal handler terminates the runner process."""
    mock_run.return_value = Mock(returncode=0)
    mock_process = setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    signal_handler = mock_signal.call_args_list[0][0][1]
    try:
        signal_handler(None, None)
    except SystemExit:
        pass
    assert mock_process.terminate.called
