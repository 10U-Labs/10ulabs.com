"""Unit tests for workflowctl CLI main() functions.

These tests verify the main() flow of each CLI command with all external
dependencies mocked (gh CLI calls, file system). Per the test tenets,
these are unit tests because they test single components (main functions)
with dependencies mocked, not cross-file compatibility.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# Test graph matching the structure used by the CLI
TEST_GRAPH = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_shared.yml", "src/www/**"],
    },
    "api_shared": {
        "name": "API Shared",
        "depends_on": ["www_shared"],
        "paths": [".github/workflows/api_shared.yml", "src/api/**"],
    },
}


@pytest.fixture
def temp_graph_file():
    """Create a temporary graph file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(TEST_GRAPH, f)
        f.flush()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


def mock_subprocess_result(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Create a mock subprocess.CompletedProcess result."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestCancelMain:
    """Integration tests for cancel.py main()."""

    def test_no_running_workflows_exits_zero(self, cancel, temp_graph_file):
        """Main returns 0 when no workflows are running."""
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "[]",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 0

    def test_invalid_running_json_exits_one(self, cancel, temp_graph_file, capsys):
        """Main returns 1 for invalid --running JSON."""
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "not-valid-json",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_missing_graph_exits_one(self, cancel, capsys):
        """Main returns 1 when graph file is missing."""
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", '["www_shared"]',
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "Error" in captured.err

    @patch("cancel.get_cancelable_runs")
    def test_no_matching_runs_exits_zero(
        self, mock_get_runs, cancel, temp_graph_file
    ):
        """Main returns 0 when no runs match workflows to cancel."""
        mock_get_runs.return_value = []
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", '["www_shared"]',
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 0

    @patch("cancel.cancel_run")
    @patch("cancel.get_cancelable_runs")
    def test_successful_cancel_exits_zero(
        self, mock_get_runs, mock_cancel, cancel, temp_graph_file
    ):
        """Main returns 0 when all cancellations succeed."""
        # get_cancelable_runs is called twice: once for in_progress, once for queued
        mock_get_runs.side_effect = [
            [{"id": 123, "name": "WWW Shared", "run_number": 1}],
            [],  # no queued runs
        ]
        mock_cancel.return_value = True
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/www/test.py",
            "--running", '["www_shared"]',
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 0
        mock_cancel.assert_called_once_with("owner/repo", 123)

    @patch("cancel.cancel_run")
    @patch("cancel.get_cancelable_runs")
    def test_failed_cancel_exits_one(
        self, mock_get_runs, mock_cancel, cancel, temp_graph_file
    ):
        """Main returns 1 when a cancellation fails."""
        mock_get_runs.side_effect = [
            [{"id": 123, "name": "WWW Shared", "run_number": 1}],
            [],  # no queued runs
        ]
        mock_cancel.return_value = False
        test_args = [
            "cancel",
            "--repo", "owner/repo",
            "--changed-files", "src/www/test.py",
            "--running", '["www_shared"]',
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = cancel.main()
        assert result == 1


class TestDispatchRootsMain:
    """Integration tests for dispatch_roots.py main()."""

    def test_missing_graph_exits_one(self, dispatch_roots, capsys):
        """Main returns 1 when graph file is missing."""
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "Error" in captured.err

    def test_invalid_running_json_exits_one(
        self, dispatch_roots, temp_graph_file, capsys
    ):
        """Main returns 1 for invalid --running JSON."""
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "not-valid-json",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_no_roots_exits_zero(self, dispatch_roots, temp_graph_file):
        """Main returns 0 when no roots need dispatching."""
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "unrelated/file.txt",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 0

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_successful_dispatch_exits_zero(
        self, mock_dispatch, mock_exists, dispatch_roots, temp_graph_file
    ):
        """Main returns 0 when dispatch succeeds."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 0
        mock_dispatch.assert_called()

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_failed_dispatch_exits_one(
        self, mock_dispatch, mock_exists, dispatch_roots, temp_graph_file
    ):
        """Main returns 1 when dispatch fails."""
        mock_exists.return_value = True
        mock_dispatch.return_value = False
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 1

    @patch("dispatch_roots.workflow_file_exists")
    def test_skips_nonexistent_workflow_file(
        self, mock_exists, dispatch_roots, temp_graph_file
    ):
        """Main skips workflows whose files don't exist."""
        mock_exists.return_value = False
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        # No dispatch attempted, so success
        assert result == 0

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_trigger_descendants_flag(
        self, mock_dispatch, mock_exists, dispatch_roots, temp_graph_file
    ):
        """Main passes trigger_descendants=True when flag is set."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--trigger-descendants",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 0
        # Verify trigger_descendants was passed as True
        mock_dispatch.assert_called_with("bootstrap", "owner/repo", True, False)

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_commit_message_triggers_descendants(
        self, mock_dispatch, mock_exists, dispatch_roots, temp_graph_file
    ):
        """Main triggers descendants when commit message contains directive."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots",
            "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--commit-message", "Fix bug [trigger descendants]",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            result = dispatch_roots.main()
        assert result == 0
        mock_dispatch.assert_called_with("bootstrap", "owner/repo", True, False)


class TestGetRunningMain:
    """Unit tests for get_running.py main()."""

    @staticmethod
    def _run_get_running(get_running, graph_file: str, capsys) -> dict:
        """Helper to run get_running.main() and return parsed JSON output."""
        test_args = ["get_running", "--repo", "owner/repo", "--graph", graph_file]
        with patch.object(sys, "argv", test_args):
            result = get_running.main()
        assert result == 0
        return json.loads(capsys.readouterr().out)

    def test_missing_graph_exits_one(self, get_running, capsys):
        """Main returns 1 when graph file is missing."""
        test_args = [
            "get_running",
            "--repo", "owner/repo",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            result = get_running.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "Error" in captured.err

    @patch("get_running.get_workflow_runs")
    def test_no_running_workflows_outputs_empty(
        self, mock_get_runs, get_running, temp_graph_file, capsys
    ):
        """Main outputs empty workflows list when none running."""
        mock_get_runs.return_value = []
        output = self._run_get_running(get_running, temp_graph_file, capsys)
        assert output == {"workflows": []}

    @patch("get_running.get_workflow_runs")
    def test_returns_running_workflow_keys(
        self, mock_get_runs, get_running, temp_graph_file, capsys
    ):
        """Main returns workflow keys for running workflows."""
        mock_get_runs.side_effect = [
            [{"name": "WWW Shared"}, {"name": "Bootstrap"}],  # in_progress
            [],  # queued
        ]
        output = self._run_get_running(get_running, temp_graph_file, capsys)
        assert set(output["workflows"]) == {"bootstrap", "www_shared"}

    @patch("get_running.get_workflow_runs")
    def test_excludes_unknown_workflows(
        self, mock_get_runs, get_running, temp_graph_file, capsys
    ):
        """Main excludes workflows not in graph."""
        mock_get_runs.side_effect = [
            [{"name": "Unknown Workflow"}, {"name": "Bootstrap"}],
            [],
        ]
        output = self._run_get_running(get_running, temp_graph_file, capsys)
        assert output["workflows"] == ["bootstrap"]


class TestComputeRootsMain:
    """Unit tests for compute_roots.py main()."""

    def test_missing_graph_exits_one(self, compute_roots):
        """Main exits 1 when graph file is missing."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                compute_roots.main()
        assert exc_info.value.code == 1

    def test_no_affected_files_outputs_empty(
        self, compute_roots, temp_graph_file, capsys
    ):
        """Main outputs empty workflows when no files match."""
        test_args = [
            "compute_roots",
            "--changed-files", "unrelated/file.txt",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"workflows": []}

    def test_outputs_root_workflow(self, compute_roots, temp_graph_file, capsys):
        """Main outputs root workflow for changed files."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"workflows": ["bootstrap"]}

    def test_start_from_overrides_file_detection(
        self, compute_roots, temp_graph_file, capsys
    ):
        """Main uses --start-from instead of file detection."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--start-from", "www_shared",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"workflows": ["www_shared"]}

    def test_invalid_start_from_exits_one(self, compute_roots, temp_graph_file):
        """Main exits 1 for unknown --start-from workflow."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--start-from", "nonexistent_workflow",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                compute_roots.main()
        assert exc_info.value.code == 1

    def test_execution_plan_includes_descendants(
        self, compute_roots, temp_graph_file, capsys
    ):
        """Main with --execution-plan includes all descendants."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--execution-plan",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # Should include bootstrap and all descendants
        assert "bootstrap" in output["workflows"]
        assert "www_shared" in output["workflows"]
        assert "api_shared" in output["workflows"]

    def test_levels_output_format(self, compute_roots, temp_graph_file, capsys):
        """Main with --levels outputs level structure."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--levels",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "levels" in output
        assert isinstance(output["levels"], list)
        # First level should have bootstrap (root)
        assert "bootstrap" in output["levels"][0]

    def test_indexed_output_format(self, compute_roots, temp_graph_file, capsys):
        """Main with --indexed outputs indexed objects."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--indexed",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "workflows" in output
        assert isinstance(output["workflows"], list)
        if output["workflows"]:
            assert "idx" in output["workflows"][0]
            assert "name" in output["workflows"][0]

    def test_slots_output_format(self, compute_roots, temp_graph_file, capsys):
        """Main with --slots outputs slot variables."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/bootstrap/main.py",
            "--execution-plan",
            "--slots", "5",
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # Should have count= and key_01= through key_05=
        assert any(line.startswith("count=") for line in lines)
        assert any(line.startswith("key_01=") for line in lines)

    def test_running_merges_with_roots(
        self, compute_roots, temp_graph_file, capsys
    ):
        """Main with --running merges running workflows with new roots."""
        test_args = [
            "compute_roots",
            "--changed-files", "src/api/main.py",
            "--running", '["bootstrap"]',
            "--graph", temp_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            compute_roots.main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # bootstrap is ancestor of api_shared, so should be the merge root
        assert "bootstrap" in output["workflows"]
