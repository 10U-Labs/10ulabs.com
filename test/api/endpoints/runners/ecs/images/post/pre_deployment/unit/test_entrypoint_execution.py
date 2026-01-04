"""Tests for entrypoint execution."""
from unittest.mock import Mock, patch
import pytest


def _setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for execution flow tests - validates run.sh behavior."""
    exec_process = Mock()
    exec_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=exec_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return exec_process


@pytest.mark.parametrize("config_returncode", [1, 127])
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_exits_with_code_1_when_config_fails(mock_run, config_returncode, entrypoint):
    """Test that main exits with code 1 when config fails with any non-zero code."""
    mock_run.return_value = Mock(returncode=config_returncode)
    try:
        entrypoint.main()
    except SystemExit as e:
        assert e.code == 1


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_run_sh_called_after_successful_configuration(mock_run, mock_popen, entrypoint):
    """Test that run.sh is called after successful configuration."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    # run.sh should be one of the Popen calls
    popen_calls = [call[0][0] for call in mock_popen.call_args_list]
    assert ['./run.sh'] in popen_calls


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_main_exits_with_run_sh_return_code(mock_run, mock_popen, entrypoint):
    """Test that main exits with run.sh return code."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen, returncode=42)
    try:
        entrypoint.main()
    except SystemExit as e:
        assert e.code == 42


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_run_sh_uses_popen(mock_run, mock_popen, entrypoint):
    """Test that run.sh uses Popen for execution."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    try:
        entrypoint.main()
    except SystemExit:
        pass
    # Popen should be called at least once (for run.sh)
    assert mock_popen.called


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_run_sh_not_called_when_config_fails(mock_run, mock_popen, entrypoint):
    """Test that run.sh is not called when config fails."""
    mock_run.return_value = Mock(returncode=1)
    with pytest.raises(SystemExit):
        entrypoint.main()
    mock_popen.assert_not_called()
