"""Unit tests for orchestrator.py CLI wiring."""

import sys
from unittest.mock import patch, MagicMock

import pytest

import orchestrator


class TestOrchestratorCLI:
    """Tests for the orchestrator CLI subcommand routing."""

    def test_no_command_shows_usage_and_returns_error(self) -> None:
        """Test that running without a command shows usage and returns 1."""
        with patch.object(sys, "argv", ["orchestrator.py"]):
            result = orchestrator.main()
        assert result == 1

    def test_unknown_command_returns_error(self) -> None:
        """Test that an unknown command returns 1."""
        with patch.object(sys, "argv", ["orchestrator.py", "unknown-command"]):
            result = orchestrator.main()
        assert result == 1

    def test_compute_roots_subcommand_routes_correctly(self) -> None:
        """Test that compute-roots subcommand routes to compute_roots.main."""
        mock_main = MagicMock(return_value=None)
        original = orchestrator.COMMANDS["compute-roots"]
        try:
            orchestrator.COMMANDS["compute-roots"] = (original[0], mock_main)
            with patch.object(sys, "argv", ["orchestrator.py", "compute-roots", "file.txt"]):
                orchestrator.main()
            mock_main.assert_called_once()
        finally:
            orchestrator.COMMANDS["compute-roots"] = original

    def test_get_running_subcommand_routes_correctly(self) -> None:
        """Test that get-running subcommand routes to get_running.main."""
        mock_main = MagicMock(return_value=0)
        original = orchestrator.COMMANDS["get-running"]
        try:
            orchestrator.COMMANDS["get-running"] = (original[0], mock_main)
            with patch.object(sys, "argv", ["orchestrator.py", "get-running", "--repo", "test/repo"]):
                result = orchestrator.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            orchestrator.COMMANDS["get-running"] = original

    def test_cancel_subcommand_routes_correctly(self) -> None:
        """Test that cancel subcommand routes to cancel.main."""
        mock_main = MagicMock(return_value=0)
        original = orchestrator.COMMANDS["cancel"]
        try:
            orchestrator.COMMANDS["cancel"] = (original[0], mock_main)
            with patch.object(sys, "argv", ["orchestrator.py", "cancel", "--repo", "test/repo", "--merge-roots", "[]"]):
                result = orchestrator.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            orchestrator.COMMANDS["cancel"] = original

    def test_dispatch_subcommand_routes_correctly(self) -> None:
        """Test that dispatch subcommand routes to dispatch.main."""
        mock_main = MagicMock(return_value=0)
        original = orchestrator.COMMANDS["dispatch"]
        try:
            orchestrator.COMMANDS["dispatch"] = (original[0], mock_main)
            with patch.object(sys, "argv", ["orchestrator.py", "dispatch", "--workflow", "test", "--repo", "test/repo"]):
                result = orchestrator.main()
            mock_main.assert_called_once()
            assert result == 0
        finally:
            orchestrator.COMMANDS["dispatch"] = original
