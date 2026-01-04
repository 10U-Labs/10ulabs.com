"""Unit tests for workflowctl.py CLI wiring."""

import sys
from unittest.mock import patch, MagicMock


class TestWorkflowctlCLI:
    """Tests for the workflowctl CLI subcommand routing."""

    def test_no_command_shows_usage_and_returns_error(self, workflowctl) -> None:
        """Test that running without a command shows usage and returns 1."""
        with patch.object(sys, "argv", ["workflowctl.py"]):
            result = workflowctl.main()
        assert result == 1

    def test_unknown_command_returns_error(self, workflowctl) -> None:
        """Test that an unknown command returns 1."""
        with patch.object(sys, "argv", ["workflowctl.py", "unknown-command"]):
            result = workflowctl.main()
        assert result == 1

    def test_compute_roots_subcommand_routes_correctly(self, workflowctl) -> None:
        """Test that compute-root-workflows subcommand routes to compute_roots.main."""
        mock_main = MagicMock(return_value=None)
        original = workflowctl.COMMANDS["compute-root-workflows"]
        try:
            workflowctl.COMMANDS["compute-root-workflows"] = (original[0], mock_main)
            argv = ["workflowctl.py", "compute-root-workflows", "file.txt"]
            with patch.object(sys, "argv", argv):
                workflowctl.main()
            mock_main.assert_called_once()
        finally:
            workflowctl.COMMANDS["compute-root-workflows"] = original
        assert True  # Explicit pass

    def test_get_running_subcommand_routes_correctly(self, workflowctl) -> None:
        """Test that get-running-workflows subcommand routes to get_running.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["get-running-workflows"]
        try:
            workflowctl.COMMANDS["get-running-workflows"] = (original[0], mock_main)
            argv = ["workflowctl.py", "get-running-workflows", "--repo", "test/repo"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["get-running-workflows"] = original

    def test_cancel_subcommand_routes_correctly(self, workflowctl) -> None:
        """Test that cancel-superseded-workflows subcommand routes to cancel.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["cancel-superseded-workflows"]
        try:
            workflowctl.COMMANDS["cancel-superseded-workflows"] = (original[0], mock_main)
            argv = ["workflowctl.py", "cancel-superseded-workflows", "--repo", "test/repo",
                    "--changed-files", "file.py"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["cancel-superseded-workflows"] = original

    def test_dispatch_subcommand_routes_correctly(self, workflowctl) -> None:
        """Test that dispatch-descendant-workflows routes to dispatch_descendants.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["dispatch-descendant-workflows"]
        try:
            workflowctl.COMMANDS["dispatch-descendant-workflows"] = (original[0], mock_main)
            argv = ["workflowctl.py", "dispatch-descendant-workflows", "--workflow", "test",
                    "--repo", "test/repo"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["dispatch-descendant-workflows"] = original

    def test_dispatch_workflow_subcommand_routes_correctly(self, workflowctl) -> None:
        """Test that dispatch-workflow routes to dispatch_workflow.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["dispatch-workflow"]
        try:
            workflowctl.COMMANDS["dispatch-workflow"] = (original[0], mock_main)
            argv = ["workflowctl.py", "dispatch-workflow", "--workflow", "test",
                    "--repo", "test/repo"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["dispatch-workflow"] = original
