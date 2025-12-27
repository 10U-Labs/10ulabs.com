"""Unit tests for cancel.py."""

from unittest.mock import MagicMock, patch


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
    "api_shared_routing": {
        "name": "API Backend",
        "depends_on": ["www_shared"],
    },
    "api_operational_health": {
        "name": "Health Endpoint",
        "depends_on": ["api_shared_routing"],
    },
}


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_leaf_has_no_descendants(self, utils) -> None:
        """Test leaf workflow has no descendants."""
        descendants = utils.get_all_descendants("api_operational_health", SAMPLE_GRAPH)
        assert descendants == set()

    def test_single_descendant(self, utils) -> None:
        """Test workflow with single direct descendant."""
        descendants = utils.get_all_descendants("api_shared_routing", SAMPLE_GRAPH)
        assert descendants == {"api_operational_health"}

    def test_transitive_descendants(self, utils) -> None:
        """Test workflow with transitive descendants."""
        descendants = utils.get_all_descendants("www_shared", SAMPLE_GRAPH)
        assert descendants == {"api_shared_routing", "api_operational_health"}

    def test_root_has_all_descendants(self, utils) -> None:
        """Test root workflow has all others as descendants."""
        descendants = utils.get_all_descendants("bootstrap", SAMPLE_GRAPH)
        assert descendants == {"www_shared", "api_shared_routing", "api_operational_health"}

    def test_caching_stores_www_shared(self, utils) -> None:
        """Test that caching stores www_shared."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "www_shared" in cache

    def test_caching_stores_api_shared_routing(self, utils) -> None:
        """Test that caching stores api_shared_routing transitively."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "api_shared_routing" in cache

    def test_caching_stores_api_operational_health(self, utils) -> None:
        """Test that caching stores api_operational_health transitively."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_shared", SAMPLE_GRAPH, cache)
        assert "api_operational_health" in cache


class TestGetWorkflowsToCancel:
    """Tests for get_workflows_to_cancel function."""

    def test_single_root_includes_descendants(self, cancel) -> None:
        """Test single merge root includes all descendants."""
        to_cancel = cancel.get_workflows_to_cancel(["www_shared"], SAMPLE_GRAPH)
        expected = {"www_shared", "api_shared_routing", "api_operational_health"}
        assert to_cancel == expected

    def test_leaf_root_includes_only_itself(self, cancel) -> None:
        """Test leaf merge root includes only itself."""
        to_cancel = cancel.get_workflows_to_cancel(["api_operational_health"], SAMPLE_GRAPH)
        assert to_cancel == {"api_operational_health"}

    def test_multiple_roots_combine_descendants(self, cancel) -> None:
        """Test multiple merge roots combine their descendants."""
        # Two independent root workflows (a, b) each with one child (c, d)
        multi_root_graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                            "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]}}
        to_cancel = cancel.get_workflows_to_cancel(["a", "b"], multi_root_graph)
        assert to_cancel == {"a", "b", "c", "d"}

    def test_empty_roots_returns_empty(self, cancel) -> None:
        """Test empty merge roots returns empty set."""
        to_cancel = cancel.get_workflows_to_cancel([], SAMPLE_GRAPH)
        assert to_cancel == set()


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_builds_correct_mapping(self, utils) -> None:
        """Test name-to-key mapping is correct."""
        name_to_key = utils.build_name_to_key_map(SAMPLE_GRAPH)
        expected = {
            "Bootstrap": "bootstrap",
            "WWW Shared": "www_shared",
            "API Backend": "api_shared_routing",
            "Health Endpoint": "api_operational_health",
        }
        assert name_to_key == expected

    def test_empty_graph_returns_empty_map(self, utils) -> None:
        """Test empty graph returns empty mapping."""
        name_to_key = utils.build_name_to_key_map({})
        assert not name_to_key


class TestCancelRun:
    """Tests for cancel_run function."""

    def test_dry_run_returns_true(self, cancel) -> None:
        """Test dry run mode returns True."""
        result = cancel.cancel_run("owner/repo", 123, dry_run=True)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_dry_run_does_not_call_subprocess(self, mock_run: MagicMock, cancel) -> None:
        """Test dry run mode doesn't call subprocess."""
        cancel.cancel_run("owner/repo", 123, dry_run=True)
        mock_run.assert_not_called()

    @patch("cancel.subprocess.run")
    def test_successful_cancel(self, mock_run: MagicMock, cancel) -> None:
        """Test successful cancellation returns True."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = cancel.cancel_run("owner/repo", 123, dry_run=False)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_already_completed_is_success(self, mock_run: MagicMock, cancel) -> None:
        """Test already completed run is treated as success."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Cannot be cancelled: run is not in progress"
        )
        result = cancel.cancel_run("owner/repo", 123, dry_run=False)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_other_error_is_failure(self, mock_run: MagicMock, cancel) -> None:
        """Test other errors return False."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Permission denied"
        )
        result = cancel.cancel_run("owner/repo", 123, dry_run=False)
        assert result is False
