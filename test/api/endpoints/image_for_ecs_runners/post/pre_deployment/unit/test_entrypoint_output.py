"""Tests for entrypoint output functionality."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


def _setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for output tests - validates print statements."""
    output_process = Mock()
    output_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=output_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return output_process


@patch('entrypoint.subprocess.Popen')
@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'my-org/my-repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_registration_prints_repository_name(mock_run, mock_print, mock_popen):
    """Test that registration prints the repository name correctly."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[1][0][0] == 'Repository: my-org/my-repo'


@patch('entrypoint.subprocess.Popen')
@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'test-runner-name',
    '--labels', 'lbl', '--token', 'tok'
])
def test_registration_prints_runner_name(mock_run, mock_print, mock_popen):
    """Test that registration prints the runner name correctly."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[2][0][0] == 'Runner Name: test-runner-name'


@patch('entrypoint.subprocess.Popen')
@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'test-labels', '--token', 'tok'
])
def test_registration_prints_labels(mock_run, mock_print, mock_popen):
    """Test that registration prints the labels correctly."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[3][0][0] == 'Labels: test-labels'


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_error_message_prints_when_config_fails(mock_run, mock_print):
    """Test that error message is printed when config.sh fails."""
    mock_run.return_value = Mock(returncode=5)
    with pytest.raises(SystemExit):
        entrypoint.main()
    error_prints = [
        c for c in mock_print.call_args_list
        if 'Error: config.sh failed' in str(c)
    ]
    assert len(error_prints) == 1


@patch('entrypoint.subprocess.Popen')
@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_runner_exit_code_is_printed(mock_run, mock_print, mock_popen):
    """Test that runner exit code is printed."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen, returncode=3)
    with pytest.raises(SystemExit):
        entrypoint.main()
    exit_code_prints = [
        c for c in mock_print.call_args_list
        if 'Runner exited with code 3' in str(c)
    ]
    assert len(exit_code_prints) == 1
