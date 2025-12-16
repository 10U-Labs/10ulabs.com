"""Tests for entrypoint cleanup_runner function."""
from unittest.mock import patch
import entrypoint


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_config_remove(mock_run):
    """Test that cleanup_runner calls config.sh --remove."""
    entrypoint.cleanup_runner('test-token')
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert './config.sh' in call_args
    assert '--remove' in call_args


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_passes_token(mock_run):
    """Test that cleanup_runner passes the token to config.sh."""
    entrypoint.cleanup_runner('my-secret-token')
    call_args = mock_run.call_args[0][0]
    assert '--token' in call_args
    assert 'my-secret-token' in call_args
