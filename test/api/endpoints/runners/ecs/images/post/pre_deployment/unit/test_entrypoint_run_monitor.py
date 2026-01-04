"""Tests for entrypoint workflow run monitor functionality."""
import json
import threading
from unittest.mock import Mock, patch
import urllib.error

import pytest


def _setup_urlopen_response(mock_urlopen, status):
    """Configure urlopen mock to return a workflow status response."""
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({"status": status}).encode()
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    mock_urlopen.return_value = mock_response


def _setup_main_mocks(mock_run, mock_popen, wait_returncode=0):
    """Configure mocks for main() execution tests."""
    mock_run.return_value = Mock(returncode=0)
    mock_process = Mock()
    mock_process.wait.return_value = wait_returncode
    mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)


class TestExtractRunIdFromName:
    """Tests for extract_run_id_from_name function."""

    def test_extracts_run_id_from_fargate_runner_name(self, entrypoint):
        """Test extracting run ID from fargate-runner-12345."""
        result = entrypoint.extract_run_id_from_name("fargate-runner-12345")
        assert result == "12345"

    def test_extracts_long_run_id(self, entrypoint):
        """Test extracting long run ID."""
        result = entrypoint.extract_run_id_from_name("fargate-runner-20387477082")
        assert result == "20387477082"

    def test_returns_none_for_non_fargate_runner(self, entrypoint):
        """Test returns None for non-fargate runner names."""
        result = entrypoint.extract_run_id_from_name("ec2-runner-12345")
        assert result is None

    def test_returns_none_for_invalid_name(self, entrypoint):
        """Test returns None for invalid runner names."""
        result = entrypoint.extract_run_id_from_name("some-other-name")
        assert result is None

    def test_returns_none_for_empty_string(self, entrypoint):
        """Test returns None for empty string."""
        result = entrypoint.extract_run_id_from_name("")
        assert result is None


class TestGetWorkflowRunStatus:
    """Tests for get_workflow_run_status function."""

    @patch('entrypoint.urllib.request.urlopen')
    def test_returns_status_on_success(self, mock_urlopen, entrypoint):
        """Test returns workflow run status on successful API call."""
        _setup_urlopen_response(mock_urlopen, "in_progress")

        result = entrypoint.get_workflow_run_status("org/repo", "12345", "token123")

        assert result == "in_progress"

    @patch('entrypoint.urllib.request.urlopen')
    def test_returns_completed_status(self, mock_urlopen, entrypoint):
        """Test returns completed status."""
        _setup_urlopen_response(mock_urlopen, "completed")

        result = entrypoint.get_workflow_run_status("org/repo", "12345", "token123")

        assert result == "completed"

    @patch('entrypoint.urllib.request.urlopen')
    def test_returns_none_on_http_error(self, mock_urlopen, entrypoint):
        """Test returns None on HTTP error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not Found", {}, None
        )

        result = entrypoint.get_workflow_run_status("org/repo", "12345", "token123")

        assert result is None

    @patch('entrypoint.urllib.request.urlopen')
    def test_returns_none_on_url_error(self, mock_urlopen, entrypoint):
        """Test returns None on URL error."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = entrypoint.get_workflow_run_status("org/repo", "12345", "token123")

        assert result is None

    @patch('entrypoint.urllib.request.urlopen')
    def test_returns_none_on_json_error(self, mock_urlopen, entrypoint):
        """Test returns None on JSON decode error."""
        mock_response = Mock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = entrypoint.get_workflow_run_status("org/repo", "12345", "token123")

        assert result is None

    @patch('entrypoint.urllib.request.Request')
    @patch('entrypoint.urllib.request.urlopen')
    def test_uses_correct_url(self, mock_urlopen, mock_request, entrypoint):
        """Test uses correct GitHub API URL."""
        _setup_urlopen_response(mock_urlopen, "queued")

        entrypoint.get_workflow_run_status("myorg/myrepo", "99999", "mytoken")

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "https://api.github.com/repos/myorg/myrepo/actions/runs/99999"

    @patch('entrypoint.urllib.request.Request')
    @patch('entrypoint.urllib.request.urlopen')
    def test_includes_authorization_header(self, mock_urlopen, mock_request, entrypoint):
        """Test includes authorization header with token."""
        _setup_urlopen_response(mock_urlopen, "queued")

        entrypoint.get_workflow_run_status("org/repo", "12345", "secret_token")

        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer secret_token"


class TestMonitorWorkflowRun:
    """Tests for monitor_workflow_run function."""

    @patch('entrypoint.get_workflow_run_status')
    @patch('entrypoint.os.kill')
    def test_sets_should_terminate_on_completed_status(
        self, _mock_kill, mock_get_status, entrypoint
    ):
        """Test sets should_terminate flag when run status is completed."""
        mock_get_status.return_value = "completed"
        stop_event = threading.Event()

        entrypoint.monitor_workflow_run("org/repo", "123", "token", stop_event, 0.01)

        assert entrypoint.monitor_state["should_terminate"] is True

    @patch('entrypoint.get_workflow_run_status')
    @patch('entrypoint.os.kill')
    def test_sends_sigterm_on_completed_status(self, mock_kill, mock_get_status, entrypoint):
        """Test sends SIGTERM when run status is completed."""
        mock_get_status.return_value = "completed"
        stop_event = threading.Event()

        entrypoint.monitor_workflow_run("org/repo", "123", "token", stop_event, 0.01)

        mock_kill.assert_called_once()
        assert True  # Explicit pass

    @patch('entrypoint.get_workflow_run_status')
    @patch('entrypoint.os.kill')
    def test_continues_on_in_progress_status(self, _mock_kill, mock_get_status, entrypoint):
        """Test continues monitoring when run is in_progress."""
        call_count = [0]

        def side_effect(*_args):
            call_count[0] += 1
            if call_count[0] >= 3:
                return "completed"
            return "in_progress"

        mock_get_status.side_effect = side_effect
        stop_event = threading.Event()

        entrypoint.monitor_workflow_run("org/repo", "123", "token", stop_event, 0.01)

        assert call_count[0] >= 3

    @patch('entrypoint.get_workflow_run_status')
    @patch('entrypoint.os.kill')
    def test_continues_on_api_error(self, _mock_kill, mock_get_status, entrypoint):
        """Test continues monitoring on API error (None status)."""
        call_count = [0]

        def side_effect(*_args):
            call_count[0] += 1
            if call_count[0] >= 3:
                return "completed"
            return None

        mock_get_status.side_effect = side_effect
        stop_event = threading.Event()

        entrypoint.monitor_workflow_run("org/repo", "123", "token", stop_event, 0.01)

        assert call_count[0] >= 3

    @patch('entrypoint.get_workflow_run_status')
    @patch('entrypoint.os.kill')
    def test_stops_when_event_is_set(self, mock_kill, mock_get_status, entrypoint):
        """Test stops monitoring when stop event is set."""
        mock_get_status.return_value = "in_progress"
        stop_event = threading.Event()
        stop_event.set()

        entrypoint.monitor_workflow_run("org/repo", "123", "token", stop_event, 0.01)

        mock_kill.assert_not_called()
        assert True  # Explicit pass


class TestStartRunMonitor:
    """Tests for start_run_monitor function."""

    def test_does_not_start_without_run_id(self, entrypoint):
        """Test does not start monitor without run_id."""
        entrypoint.start_run_monitor("org/repo", "", "token", 30)

        assert entrypoint.monitor_state["stop_event"] is None

    def test_does_not_start_without_github_token(self, entrypoint):
        """Test does not start monitor without github_token."""
        entrypoint.start_run_monitor("org/repo", "12345", "", 30)

        assert entrypoint.monitor_state["stop_event"] is None

    @patch('entrypoint.threading.Thread')
    def test_creates_thread(self, mock_thread_class, entrypoint):
        """Test creates a thread for monitoring."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        entrypoint.start_run_monitor("org/repo", "12345", "token", 30)

        mock_thread_class.assert_called_once()
        assert True  # Explicit pass

    @patch('entrypoint.threading.Thread')
    def test_creates_daemon_thread(self, mock_thread_class, entrypoint):
        """Test creates thread with daemon=True."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        entrypoint.start_run_monitor("org/repo", "12345", "token", 30)

        call_kwargs = mock_thread_class.call_args[1]
        assert call_kwargs["daemon"] is True

    @patch('entrypoint.threading.Thread')
    def test_starts_thread(self, mock_thread_class, entrypoint):
        """Test starts the monitoring thread."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        entrypoint.start_run_monitor("org/repo", "12345", "token", 30)

        mock_thread.start.assert_called_once()
        assert True  # Explicit pass

    @patch('entrypoint.threading.Thread')
    def test_sets_stop_event(self, mock_thread_class, entrypoint):
        """Test sets stop event in monitor state."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        entrypoint.start_run_monitor("org/repo", "12345", "token", 30)

        assert entrypoint.monitor_state["stop_event"] is not None

    @patch('entrypoint.threading.Thread')
    def test_stop_event_is_threading_event(self, mock_thread_class, entrypoint):
        """Test stop event is a threading.Event instance."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        entrypoint.start_run_monitor("org/repo", "12345", "token", 30)

        assert isinstance(entrypoint.monitor_state["stop_event"], threading.Event)


class TestStopRunMonitor:
    """Tests for stop_run_monitor function."""

    def test_sets_stop_event(self, entrypoint):
        """Test sets the stop event."""
        stop_event = threading.Event()
        entrypoint.monitor_state["stop_event"] = stop_event

        entrypoint.stop_run_monitor()

        assert stop_event.is_set()

    def test_handles_no_stop_event(self, entrypoint):
        """Test handles case where stop event is None."""
        entrypoint.monitor_state["stop_event"] = None

        # Should not raise
        entrypoint.stop_run_monitor()
        assert True  # Explicit pass


class TestMainWithRunMonitor:
    """Tests for main function with run monitor integration."""

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.start_run_monitor')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'fargate-runner-12345',
        '--labels', 'lbl', '--token', 'tok'
    ])
    def test_starts_run_monitor_with_fargate_runner(
        self, mock_run, mock_start_monitor, mock_popen, entrypoint
    ):
        """Test starts run monitor for fargate runner with token."""
        _setup_main_mocks(mock_run, mock_popen)

        with pytest.raises(SystemExit):
            entrypoint.main()

        mock_start_monitor.assert_called_once_with("org/repo", "12345", "test_token", 30)

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.start_run_monitor')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {}, clear=True)
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'fargate-runner-12345',
        '--labels', 'lbl', '--token', 'tok'
    ])
    def test_does_not_start_monitor_without_github_token(
        self, mock_run, mock_start_monitor, mock_popen, entrypoint
    ):
        """Test does not start run monitor without GITHUB_TOKEN env var."""
        _setup_main_mocks(mock_run, mock_popen)

        with pytest.raises(SystemExit):
            entrypoint.main()

        mock_start_monitor.assert_not_called()

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.start_run_monitor')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'ec2-runner-12345',
        '--labels', 'lbl', '--token', 'tok'
    ])
    def test_does_not_start_monitor_for_ec2_runner(
        self, mock_run, mock_start_monitor, mock_popen, entrypoint
    ):
        """Test does not start run monitor for non-fargate runner."""
        _setup_main_mocks(mock_run, mock_popen)

        with pytest.raises(SystemExit):
            entrypoint.main()

        mock_start_monitor.assert_not_called()

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.stop_run_monitor')
    @patch('entrypoint.start_run_monitor')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'fargate-runner-12345',
        '--labels', 'lbl', '--token', 'tok'
    ])
    def test_stops_run_monitor_on_exit(
        self, mock_run, _mock_start_monitor, mock_stop_monitor, mock_popen, entrypoint
    ):
        """Test stops run monitor when main exits."""
        _setup_main_mocks(mock_run, mock_popen)

        with pytest.raises(SystemExit):
            entrypoint.main()

        mock_stop_monitor.assert_called()

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.start_run_monitor')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'fargate-runner-12345',
        '--labels', 'lbl', '--token', 'tok', '--check-interval', '60'
    ])
    def test_uses_custom_check_interval(
        self, mock_run, mock_start_monitor, mock_popen, entrypoint
    ):
        """Test uses custom check interval from argument."""
        _setup_main_mocks(mock_run, mock_popen)

        with pytest.raises(SystemExit):
            entrypoint.main()

        mock_start_monitor.assert_called_once_with("org/repo", "12345", "test_token", 60)

    @patch('entrypoint.subprocess.Popen')
    @patch('entrypoint.stop_run_monitor')
    @patch('entrypoint.signal.signal')
    @patch('entrypoint.subprocess.run')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'fargate-runner-12345',
        '--labels', 'lbl', '--token', 'tok'
    ])
    def test_signal_handler_stops_run_monitor(
        self, mock_run, mock_signal, mock_stop_monitor, mock_popen, entrypoint
    ):
        """Test signal handler stops run monitor."""
        _setup_main_mocks(mock_run, mock_popen)

        try:
            entrypoint.main()
        except SystemExit:
            pass

        # Get the signal handler
        signal_handler = mock_signal.call_args_list[0][0][1]

        mock_stop_monitor.reset_mock()

        try:
            signal_handler(None, None)
        except SystemExit:
            pass

        assert mock_stop_monitor.call_count == 1
