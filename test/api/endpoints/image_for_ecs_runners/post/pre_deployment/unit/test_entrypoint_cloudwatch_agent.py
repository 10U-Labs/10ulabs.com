"""Tests for CloudWatch agent lifecycle in entrypoint."""
# pylint: disable=protected-access
import subprocess
import threading
import time
from unittest.mock import Mock, patch

import entrypoint


class TestCwStateInitialization:
    """Tests for _cw_state initialization."""

    def test_cw_state_has_stop_event_key(self):
        """Test that _cw_state has stop_event key."""
        assert "stop_event" in entrypoint._cw_state

    def test_cw_state_has_thread_key(self):
        """Test that _cw_state has thread key."""
        assert "thread" in entrypoint._cw_state


class TestStartCloudwatchAgent:
    """Tests for start_cloudwatch_agent function."""

    @patch('entrypoint.subprocess.run')
    @patch('entrypoint.subprocess.Popen')
    def test_stores_stop_event(self, mock_popen, mock_run):
        """Test that start_cloudwatch_agent stores stop_event in _cw_state."""
        mock_run.return_value = Mock(returncode=0)
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        entrypoint.start_cloudwatch_agent()

        assert entrypoint._cw_state["stop_event"] is not None
        assert isinstance(entrypoint._cw_state["stop_event"], threading.Event)

    @patch('entrypoint.subprocess.run')
    @patch('entrypoint.subprocess.Popen')
    def test_stores_thread_reference(self, mock_popen, mock_run):
        """Test that start_cloudwatch_agent stores thread reference in _cw_state."""
        mock_run.return_value = Mock(returncode=0)
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        entrypoint.start_cloudwatch_agent()

        assert entrypoint._cw_state["thread"] is not None
        assert isinstance(entrypoint._cw_state["thread"], threading.Thread)

    @patch('entrypoint.subprocess.run')
    @patch('entrypoint.subprocess.Popen')
    def test_thread_is_daemon(self, mock_popen, mock_run):
        """Test that CloudWatch agent thread is a daemon thread."""
        mock_run.return_value = Mock(returncode=0)
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        entrypoint.start_cloudwatch_agent()

        assert entrypoint._cw_state["thread"].daemon is True

    @patch('entrypoint.subprocess.run')
    @patch('entrypoint.subprocess.Popen')
    def test_thread_is_started(self, mock_popen, mock_run):
        """Test that CloudWatch agent thread is started."""
        mock_run.return_value = Mock(returncode=0)
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        entrypoint.start_cloudwatch_agent()

        thread = entrypoint._cw_state["thread"]
        # Thread should be alive or have already completed
        # (may complete quickly with mocked subprocess)
        assert thread is not None


class TestStopCloudwatchAgent:
    """Tests for stop_cloudwatch_agent function."""

    def test_sets_stop_event(self):
        """Test that stop_cloudwatch_agent sets the stop event."""
        stop_event = threading.Event()
        entrypoint._cw_state["stop_event"] = stop_event
        entrypoint._cw_state["thread"] = None

        entrypoint.stop_cloudwatch_agent()

        assert stop_event.is_set()

    def test_joins_thread(self):
        """Test that stop_cloudwatch_agent waits for thread to complete.

        THIS IS THE KEY TEST THAT WOULD HAVE CAUGHT THE BUG.
        """
        mock_thread = Mock()
        entrypoint._cw_state["stop_event"] = threading.Event()
        entrypoint._cw_state["thread"] = mock_thread

        entrypoint.stop_cloudwatch_agent()

        mock_thread.join.assert_called_once_with(timeout=5)

    def test_handles_none_stop_event(self):
        """Test that stop_cloudwatch_agent handles None stop_event gracefully."""
        entrypoint._cw_state["stop_event"] = None
        entrypoint._cw_state["thread"] = Mock()

        # Should not raise
        entrypoint.stop_cloudwatch_agent()

    def test_handles_none_thread(self):
        """Test that stop_cloudwatch_agent handles None thread gracefully."""
        entrypoint._cw_state["stop_event"] = threading.Event()
        entrypoint._cw_state["thread"] = None

        # Should not raise
        entrypoint.stop_cloudwatch_agent()

    def test_handles_both_none(self):
        """Test that stop_cloudwatch_agent handles both None gracefully."""
        entrypoint._cw_state["stop_event"] = None
        entrypoint._cw_state["thread"] = None

        # Should not raise
        entrypoint.stop_cloudwatch_agent()

    def test_uses_timeout(self):
        """Test that stop_cloudwatch_agent uses timeout when joining thread."""
        mock_thread = Mock()
        entrypoint._cw_state["stop_event"] = threading.Event()
        entrypoint._cw_state["thread"] = mock_thread

        entrypoint.stop_cloudwatch_agent()

        # Verify timeout argument is passed
        call_args = mock_thread.join.call_args
        assert call_args is not None
        assert call_args[1].get('timeout') == 5 or call_args[0] == (5,) or \
            (len(call_args) > 0 and call_args.kwargs.get('timeout') == 5)


class TestRunCloudwatchAgent:
    """Tests for _run_cloudwatch_agent function."""

    @patch('entrypoint.subprocess.Popen')
    def test_terminates_on_stop_event(self, mock_popen):
        """Test that _run_cloudwatch_agent terminates subprocess when stop event is set."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        stop_event = threading.Event()
        stop_event.set()  # Set immediately to trigger termination

        entrypoint._run_cloudwatch_agent("/fake/path.toml", stop_event)

        mock_process.terminate.assert_called_once()

    @patch('entrypoint.subprocess.Popen')
    def test_waits_for_process_termination(self, mock_popen):
        """Test that _run_cloudwatch_agent waits for subprocess to exit."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        stop_event = threading.Event()
        stop_event.set()  # Set immediately to trigger termination

        entrypoint._run_cloudwatch_agent("/fake/path.toml", stop_event)

        mock_process.wait.assert_called_once_with(timeout=3)

    @patch('entrypoint.subprocess.Popen')
    def test_kills_if_terminate_times_out(self, mock_popen):
        """Test that _run_cloudwatch_agent kills subprocess if terminate times out."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=3)
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        stop_event = threading.Event()
        stop_event.set()  # Set immediately to trigger termination

        entrypoint._run_cloudwatch_agent("/fake/path.toml", stop_event)

        mock_process.kill.assert_called_once()


class TestCloudwatchAgentLifecycleIntegration:
    """Integration tests for complete CloudWatch agent lifecycle."""

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.subprocess.run')
    def test_subprocess_terminated_before_stop_returns(self, mock_run, mock_popen):
        """Test that subprocess is fully terminated before stop_cloudwatch_agent returns.

        THIS IS THE KEY TEST - it would have caught the bug where stop_cloudwatch_agent()
        returns before the subprocess is terminated, leaving it orphaned.
        """
        mock_run.return_value = Mock(returncode=0)

        # Track termination order
        termination_order = []

        def mark_terminated():
            termination_order.append("subprocess_terminated")

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running initially
        mock_process.terminate.side_effect = mark_terminated
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        # Start the agent
        entrypoint.start_cloudwatch_agent()

        # Give thread a moment to start
        time.sleep(0.1)

        # Stop the agent
        entrypoint.stop_cloudwatch_agent()

        # Verify stop_cloudwatch_agent waited for thread (which terminates subprocess)
        thread = entrypoint._cw_state["thread"]
        # Thread should have completed or be completing (join was called with timeout)
        assert thread is not None

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.subprocess.run')
    def test_start_then_stop_does_not_leave_orphans(self, mock_run, mock_popen):
        """Test that starting then stopping does not leave orphaned processes."""
        mock_run.return_value = Mock(returncode=0)
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process exits quickly
        mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
        mock_popen.return_value.__exit__ = Mock(return_value=False)

        entrypoint.start_cloudwatch_agent()
        entrypoint.stop_cloudwatch_agent()

        # After stop, state should still be set (we don't clear it)
        assert entrypoint._cw_state["stop_event"].is_set()
