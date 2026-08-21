"""Unit tests for cancel.py."""
import sys

from typing import Any, Dict
from unittest.mock import MagicMock, patch


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_leaf_has_no_descendants(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test leaf workflow has no descendants."""
        descendants = utils.get_all_descendants("api_operational_health", sample_graph)
        assert descendants == set()

    def test_single_descendant(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test workflow with single direct descendant."""
        descendants = utils.get_all_descendants("api_common_routing", sample_graph)
        assert descendants == {"api_operational_health"}

    def test_transitive_descendants(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test workflow with transitive descendants."""
        descendants = utils.get_all_descendants("www_common", sample_graph)
        assert descendants == {"api_common_routing", "api_operational_health"}

    def test_root_has_all_descendants(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test root workflow has all others as descendants."""
        descendants = utils.get_all_descendants("bootstrap", sample_graph)
        assert descendants == {"www_common", "api_common_routing", "api_operational_health"}

    def test_caching_stores_www_common(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test that caching stores www_common."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_common", sample_graph, cache)
        assert "www_common" in cache

    def test_caching_stores_api_common_routing(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test that caching stores api_common_routing transitively."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_common", sample_graph, cache)
        assert "api_common_routing" in cache

    def test_caching_stores_api_operational_health(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test that caching stores api_operational_health transitively."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("www_common", sample_graph, cache)
        assert "api_operational_health" in cache


class TestGetWorkflowsToCancel:
    """Tests for get_workflows_to_cancel function."""

    def test_single_root_includes_descendants(
        self, cancel, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test single merge root includes all descendants."""
        to_cancel = cancel.get_workflows_to_cancel(["www_common"], sample_graph)
        expected = {"www_common", "api_common_routing", "api_operational_health"}
        assert to_cancel == expected

    def test_leaf_root_includes_only_itself(
        self, cancel, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test leaf merge root includes only itself."""
        to_cancel = cancel.get_workflows_to_cancel(["api_operational_health"], sample_graph)
        assert to_cancel == {"api_operational_health"}

    def test_multiple_roots_combine_descendants(self, cancel) -> None:
        """Test multiple merge roots combine their descendants."""
        # Two independent root workflows (a, b) each with one child (c, d)
        multi_root_graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                            "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]}}
        to_cancel = cancel.get_workflows_to_cancel(["a", "b"], multi_root_graph)
        assert to_cancel == {"a", "b", "c", "d"}

    def test_empty_roots_returns_empty(
        self, cancel, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test empty merge roots returns empty set."""
        to_cancel = cancel.get_workflows_to_cancel([], sample_graph)
        assert to_cancel == set()


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_builds_correct_mapping(
        self, utils, sample_graph: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test name-to-key mapping is correct."""
        name_to_key = utils.build_name_to_key_map(sample_graph)
        expected = {
            "Bootstrap": "bootstrap",
            "WWW Common": "www_common",
            "API Common Routing": "api_common_routing",
            "API Operational Health": "api_operational_health",
        }
        assert name_to_key == expected

    def test_empty_graph_returns_empty_map(self, utils) -> None:
        """Test empty graph returns empty mapping."""
        name_to_key = utils.build_name_to_key_map({})
        assert not name_to_key


class TestCancelRun:
    """Tests for cancel_run function."""

    @patch("cancel.subprocess.run")
    def test_successful_cancel(self, mock_run: MagicMock, cancel) -> None:
        """Test successful cancellation returns True."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = cancel.cancel_run("owner/repo", 123)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_completed_run_is_success(self, mock_run: MagicMock, cancel) -> None:
        """Test a run that completed before the cancel is treated as success.

        The stderr is quoted verbatim from `gh run cancel` against a run that
        has already finished, which is the race this guard exists to absorb.
        """
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Cannot cancel a workflow run that is completed"
        )
        result = cancel.cancel_run("owner/repo", 123)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_queued_run_is_success(self, mock_run: MagicMock, cancel) -> None:
        """Test a run GitHub reports as queued is treated as success.

        The stderr is quoted verbatim from `gh run cancel`; a queued run that
        starts and finishes is the same race, worded differently.
        """
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Cannot cancel a workflow run that is queued"
        )
        result = cancel.cancel_run("owner/repo", 123)
        assert result is True

    @patch("cancel.subprocess.run")
    def test_other_error_is_failure(self, mock_run: MagicMock, cancel) -> None:
        """Test other errors return False."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Permission denied"
        )
        result = cancel.cancel_run("owner/repo", 123)
        assert result is False


class TestGetCancelableRuns:
    """Tests for get_cancelable_runs function."""

    @patch("cancel.get_workflow_runs")
    def test_extracts_required_fields(
        self, mock_get_runs: MagicMock, cancel
    ) -> None:
        """Test that only id, name, run_number are extracted."""
        mock_get_runs.return_value = [
            {"id": 1, "name": "Test", "run_number": 42, "extra": "ignored", "status": "in_progress"}
        ]
        result = cancel.get_cancelable_runs("owner/repo", "in_progress")
        assert result == [{"id": 1, "name": "Test", "run_number": 42}]

    @patch("cancel.get_workflow_runs")
    def test_handles_empty_runs(self, mock_get_runs: MagicMock, cancel) -> None:
        """Test empty runs returns empty list."""
        mock_get_runs.return_value = []
        result = cancel.get_cancelable_runs("owner/repo", "in_progress")
        assert result == []


class TestMainEdgeCases:
    """Edge case tests for main function."""

    def test_returns_0_when_no_merge_roots(self, cancel) -> None:
        """Test returns 0 when compute_merge_roots returns empty."""
        argv = [
            "prog", "--running", '["api"]',
            "--graph", "g.json", "--repo", "o/r", "--changed-files", ""
        ]
        with patch.object(sys, "argv", argv):
            with patch(
                "cancel.parse_running_workflows",
                return_value=(["api"], None)
            ):
                with patch(
                    "cancel.load_graph_and_compute_roots",
                    return_value=({"bootstrap": {}}, ["bootstrap"], None)
                ):
                    with patch(
                        "cancel.compute_merge_roots",
                        return_value=[]
                    ):
                        result = cancel.main()
        assert result == 0

    @patch("cancel.subprocess.run")
    @patch("cancel.get_cancelable_runs")
    def test_returns_0_when_the_only_failure_is_a_completed_run(
        self, mock_get_runs: MagicMock, mock_subprocess: MagicMock, cancel
    ) -> None:
        """Test returns 0 when every cancellation that failed had already finished.

        The step's exit code is what gates the dispatch of the root workflows,
        so a run that finished mid-cancel must not stop the whole push.
        """
        graph = {"www_common": {"name": "WWW Common", "depends_on": []}}
        mock_get_runs.side_effect = [
            [{"id": 123, "name": "WWW Common", "run_number": 1}], []
        ]
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stderr="Cannot cancel a workflow run that is completed"
        )
        argv = [
            "prog", "--running", '["www_common"]',
            "--graph", "g.json", "--repo", "o/r", "--changed-files", ""
        ]
        with patch.object(sys, "argv", argv), patch(
            "cancel.load_graph_and_compute_roots",
            return_value=(graph, ["www_common"], None)
        ), patch("cancel.compute_merge_roots", return_value=["www_common"]):
            result = cancel.main()
        assert result == 0
