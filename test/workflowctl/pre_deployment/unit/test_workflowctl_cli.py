"""Unit tests for workflowctl.py CLI wiring."""

import sys
from unittest.mock import patch, MagicMock

import workflowctl


class TestWorkflowctlCLI:
    """Tests for the workflowctl CLI subcommand routing."""

    def test_no_command_shows_usage_and_returns_error(self) -> None:
        """Test that running without a command shows usage and returns 1."""
        with patch.object(sys, "argv", ["workflowctl.py"]):
            result = workflowctl.main()
        assert result == 1

    def test_unknown_command_returns_error(self) -> None:
        """Test that an unknown command returns 1."""
        with patch.object(sys, "argv", ["workflowctl.py", "unknown-command"]):
            result = workflowctl.main()
        assert result == 1

    def test_compute_roots_subcommand_routes_correctly(self) -> None:
        """Test that compute-roots subcommand routes to compute_roots.main."""
        mock_main = MagicMock(return_value=None)
        original = workflowctl.COMMANDS["compute-roots"]
        try:
            workflowctl.COMMANDS["compute-roots"] = (original[0], mock_main)
            with patch.object(sys, "argv", ["workflowctl.py", "compute-roots", "file.txt"]):
                workflowctl.main()
            mock_main.assert_called_once()
        finally:
            workflowctl.COMMANDS["compute-roots"] = original

    def test_get_running_subcommand_routes_correctly(self) -> None:
        """Test that get-running subcommand routes to get_running.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["get-running"]
        try:
            workflowctl.COMMANDS["get-running"] = (original[0], mock_main)
            argv = ["workflowctl.py", "get-running", "--repo", "test/repo"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["get-running"] = original

    def test_cancel_subcommand_routes_correctly(self) -> None:
        """Test that cancel subcommand routes to cancel.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["cancel"]
        try:
            workflowctl.COMMANDS["cancel"] = (original[0], mock_main)
            argv = ["workflowctl.py", "cancel", "--repo", "test/repo",
                    "--merge-roots", "[]"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["cancel"] = original

    def test_dispatch_subcommand_routes_correctly(self) -> None:
        """Test that dispatch subcommand routes to dispatch.main."""
        mock_main = MagicMock(return_value=0)
        original = workflowctl.COMMANDS["dispatch"]
        try:
            workflowctl.COMMANDS["dispatch"] = (original[0], mock_main)
            argv = ["workflowctl.py", "dispatch", "--workflow", "test",
                    "--repo", "test/repo"]
            with patch.object(sys, "argv", argv):
                result = workflowctl.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            workflowctl.COMMANDS["dispatch"] = original
