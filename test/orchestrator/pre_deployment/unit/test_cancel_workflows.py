"""Unit tests for cancel_workflows.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from cancel_workflows import (
    cancel_run,
    get_workflows_to_cancel,
)
from workflow_utils import (
    build_name_to_key_map,
    get_all_descendants,
)


# Sample dependency graph for testing
SAMPLE_GRAPH = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
    },
    "api_backend": {
        "name": "API Backend",
        "depends_on": ["www_shared"],
    },
    "operational_health": {
        "name": "Health Endpoint",
        "depends_on": ["api_backend"],
    },
}


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_leaf_has_no_descendants(self) -> None:
        """Test leaf workflow has no descendants."""
        descendants = get_all_descendants("operational_health", SAMPLE_GRAPH)
        assert descendants == set()

    def test_single_descendant(self) -> None:
        """Test workflow with single direct descendant."""
        descendants = get_all_descendants("api_backend", SAMPLE_GRAPH)
        assert descendants == {"operational_health"}

    def test_transitive_descendants(self) -> None:
        """Test workflow with transitive descendants."""
        descendants = get_all_descendants("www_shared", SAMPLE_GRAPH)
        assert descendants == {"api_backend", "operational_health"}

    def test_root_has_all_descendants(self) -> None:
        """Test root workflow has all others as descendants."""
        descendants = get_all_descendants("bootstrap", SAMPLE_GRAPH)
        assert descendants == {"www_shared", "api_backend", "operational_health"}

    def test_caching_stores_www_shared(self) -> None:
        """Test that caching stores www_shared."""
        cache: dict[str, set[str]] = {}
        get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "www_shared" in cache

    def test_caching_stores_api_backend(self) -> None:
        """Test that caching stores api_backend transitively."""
        cache: dict[str, set[str]] = {}
        get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "api_backend" in cache

    def test_caching_stores_operational_health(self) -> None:
        """Test that caching stores operational_health transitively."""
        cache: dict[str, set[str]] = {}
        get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "operational_health" in cache


class TestGetWorkflowsToCancel:
    """Tests for get_workflows_to_cancel function."""

    def test_single_root_includes_descendants(self) -> None:
        """Test single merge root includes all descendants."""
        to_cancel = get_workflows_to_cancel(["www_shared"], SAMPLE_GRAPH)
        expected = {"www_shared", "api_backend", "operational_health"}
        assert to_cancel == expected

    def test_leaf_root_includes_only_itself(self) -> None:
        """Test leaf merge root includes only itself."""
        to_cancel = get_workflows_to_cancel(["operational_health"], SAMPLE_GRAPH)
        assert to_cancel == {"operational_health"}

    def test_multiple_roots_combine_descendants(self) -> None:
        """Test multiple merge roots combine their descendants."""
        graph = {
            "a": {"depends_on": []},
            "b": {"depends_on": []},
            "c": {"depends_on": ["a"]},
            "d": {"depends_on": ["b"]},
        }
        to_cancel = get_workflows_to_cancel(["a", "b"], graph)
        assert to_cancel == {"a", "b", "c", "d"}

    def test_empty_roots_returns_empty(self) -> None:
        """Test empty merge roots returns empty set."""
        to_cancel = get_workflows_to_cancel([], SAMPLE_GRAPH)
        assert to_cancel == set()


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_builds_correct_mapping(self) -> None:
        """Test name-to-key mapping is correct."""
        name_to_key = build_name_to_key_map(SAMPLE_GRAPH)
        expected = {
            "Bootstrap": "bootstrap",
            "WWW Shared": "www_shared",
            "API Backend": "api_backend",
            "Health Endpoint": "operational_health",
        }
        assert name_to_key == expected


class TestCancelRun:
    """Tests for cancel_run function."""

    def test_dry_run_returns_true(self) -> None:
        """Test dry run mode returns True."""
        result = cancel_run("owner/repo", 123, dry_run=True)
        assert result is True

    @patch("cancel_workflows.subprocess.run")
    def test_dry_run_does_not_call_subprocess(self, mock_run: MagicMock) -> None:
        """Test dry run mode doesn't call subprocess."""
        cancel_run("owner/repo", 123, dry_run=True)
        mock_run.assert_not_called()

    @patch("cancel_workflows.subprocess.run")
    def test_successful_cancel(self, mock_run: MagicMock) -> None:
        """Test successful cancellation returns True."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = cancel_run("owner/repo", 123, dry_run=False)
        assert result is True

    @patch("cancel_workflows.subprocess.run")
    def test_already_completed_is_success(self, mock_run: MagicMock) -> None:
        """Test already completed run is treated as success."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Cannot be cancelled: run is not in progress"
        )
        result = cancel_run("owner/repo", 123, dry_run=False)
        assert result is True

    @patch("cancel_workflows.subprocess.run")
    def test_other_error_is_failure(self, mock_run: MagicMock) -> None:
        """Test other errors return False."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Permission denied"
        )
        result = cancel_run("owner/repo", 123, dry_run=False)
        assert result is False
