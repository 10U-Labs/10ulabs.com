"""Unit tests for orchestrator.py CLI wiring."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO_ROOT = _find_repo_root()

# Add src/orchestrator directory to path for imports
sys.path.insert(0, str(REPO_ROOT / "src" / "orchestrator"))

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
        mock_main = MagicMock()
        with patch.object(sys, "argv", ["orchestrator.py", "compute-roots", "file.txt"]):
            with patch.object(orchestrator.compute_roots, "main", mock_main):
                orchestrator.main()
        mock_main.assert_called_once()

    def test_get_running_subcommand_routes_correctly(self) -> None:
        """Test that get-running subcommand routes to get_running.main."""
        mock_main = MagicMock(return_value=0)
        with patch.object(sys, "argv", ["orchestrator.py", "get-running", "--repo", "test/repo"]):
            with patch.object(orchestrator.get_running, "main", mock_main):
                result = orchestrator.main()
        mock_main.assert_called_once()
        assert result == 0

    def test_cancel_subcommand_routes_correctly(self) -> None:
        """Test that cancel subcommand routes to cancel.main."""
        mock_main = MagicMock(return_value=0)
        with patch.object(sys, "argv", ["orchestrator.py", "cancel", "--repo", "test/repo", "--merge-roots", "[]"]):
            with patch.object(orchestrator.cancel, "main", mock_main):
                result = orchestrator.main()
        mock_main.assert_called_once()
        assert result == 0

    def test_dispatch_subcommand_routes_correctly(self) -> None:
        """Test that dispatch subcommand routes to dispatch.main."""
        mock_main = MagicMock(return_value=0)
        with patch.object(sys, "argv", ["orchestrator.py", "dispatch", "--workflow", "test", "--repo", "test/repo"]):
            with patch.object(orchestrator.dispatch, "main", mock_main):
                result = orchestrator.main()
        mock_main.assert_called_once()
        assert result == 0
