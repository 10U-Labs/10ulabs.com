"""Tests for entrypoint cleanup_runner function."""
from unittest.mock import patch
import entrypoint


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_subprocess_run(mock_run):
    """Test that cleanup_runner calls subprocess.run."""
    entrypoint.cleanup_runner('test-token')
    mock_run.assert_called_once()


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_config_sh(mock_run):
    """Test that cleanup_runner calls config.sh."""
    entrypoint.cleanup_runner('test-token')
    assert './config.sh' in mock_run.call_args[0][0]


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_passes_remove_flag(mock_run):
    """Test that cleanup_runner passes --remove flag."""
    entrypoint.cleanup_runner('test-token')
    assert '--remove' in mock_run.call_args[0][0]


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_passes_token_flag(mock_run):
    """Test that cleanup_runner passes --token flag."""
    entrypoint.cleanup_runner('my-secret-token')
    assert '--token' in mock_run.call_args[0][0]


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_passes_token_value(mock_run):
    """Test that cleanup_runner passes the token value."""
    entrypoint.cleanup_runner('my-secret-token')
    assert 'my-secret-token' in mock_run.call_args[0][0]
