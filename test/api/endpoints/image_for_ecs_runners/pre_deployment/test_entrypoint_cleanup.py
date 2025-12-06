"""Tests for entrypoint cleanup functionality."""
from unittest.mock import Mock, patch
import entrypoint


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_subprocess_run_with_config_sh(mock_run):
    """Test that cleanup_runner calls subprocess.run with config.sh."""
    entrypoint.cleanup_runner('test-token')
    assert mock_run.called


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_uses_registration_token_parameter(mock_run):
    """Test that cleanup_runner uses registration token parameter."""
    entrypoint.cleanup_runner('my-token')
    assert mock_run.call_args[0][0][3] == 'my-token'


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_uses_check_false_parameter(mock_run):
    """Test that cleanup_runner uses check=False parameter."""
    entrypoint.cleanup_runner('token')
    assert mock_run.call_args[1]['check'] is False


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_continues_when_removal_fails(mock_run):
    """Test that cleanup_runner continues when removal fails."""
    mock_run.return_value = Mock(returncode=1)
    entrypoint.cleanup_runner('token')
    assert mock_run.called


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_config_sh_remove(mock_run):
    """Test that cleanup_runner calls config.sh remove."""
    entrypoint.cleanup_runner('test-token')
    assert mock_run.call_args[0][0][1] == 'remove'
