"""Unit tests for dispatch_descendants.py."""

import sys
from datetime import datetime, timezone
from typing import Any, Tuple
from unittest.mock import patch, MagicMock


def _run_main_with_unmet_deps(dispatch_descendants: Any) -> Tuple[int, MagicMock]:
    """Run main() with unmet dependencies and return (result, mock_dispatch)."""
    argv = ["prog", "--workflow", "www_common", "--repo", "o/r"]
    mock_dispatch = MagicMock()
    with patch.object(sys, "argv", argv):
        with patch(
            "dispatch_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
        ):
            with patch(
                "dispatch_descendants.all_dependencies_met",
                return_value=(False, ["api_common"])
            ):
                with patch("dispatch_descendants.dispatch_workflow", mock_dispatch):
                    result = dispatch_descendants.main()
    return result, mock_dispatch


SAMPLE_GRAPH = {
    "bootstrap": {"name": "Bootstrap", "depends_on": []},
    "www_common": {"name": "WWW Common", "depends_on": ["bootstrap"]},
    "api_common": {"name": "API Common", "depends_on": ["bootstrap"]},
    "www_app": {"name": "WWW App", "depends_on": ["www_common", "api_common"]},
}


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parses_workflow_argument(self, dispatch_descendants) -> None:
        """Test that --workflow argument is parsed correctly."""
        argv = ["prog", "--workflow", "bootstrap", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.workflow == "bootstrap"

    def test_parses_repo_argument(self, dispatch_descendants) -> None:
        """Test that --repo argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.repo == "owner/repo"

    def test_graph_defaults_to_standard_path(self, dispatch_descendants) -> None:
        """Test that --graph defaults to etc/workflow_dependencies.json."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.graph == "etc/workflow_dependencies.json"

    def test_parses_custom_graph_path(self, dispatch_descendants) -> None:
        """Test that --graph argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--graph", "custom.json"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.graph == "custom.json"

    def test_lookback_hours_defaults_to_24(self, dispatch_descendants) -> None:
        """Test that --lookback-hours defaults to 24."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.lookback_hours == 24

    def test_parses_lookback_hours(self, dispatch_descendants) -> None:
        """Test that --lookback-hours argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--lookback-hours", "48"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.lookback_hours == 48

    def test_trigger_descendants_defaults_to_false(self, dispatch_descendants) -> None:
        """Test that --trigger-descendants defaults to False."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.trigger_descendants is False

    def test_trigger_descendants_true_when_flag_present(
        self, dispatch_descendants
    ) -> None:
        """Test that --trigger-descendants sets flag to True."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--trigger-descendants"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.trigger_descendants is True

    def test_invalidate_cloudfront_defaults_to_false(
        self, dispatch_descendants
    ) -> None:
        """Test that --invalidate-cloudfront defaults to False."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.invalidate_cloudfront is False

    def test_invalidate_cloudfront_true_when_flag_present(
        self, dispatch_descendants
    ) -> None:
        """Test that --invalidate-cloudfront sets flag to True."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--invalidate-cloudfront"]
        with patch.object(sys, "argv", argv):
            args = dispatch_descendants.parse_args()
        assert args.invalidate_cloudfront is True


class TestFindDescendants:
    """Tests for find_descendants function."""

    def test_returns_empty_for_leaf_workflow(self, dispatch_descendants) -> None:
        """Test that a leaf workflow has no descendants."""
        result = dispatch_descendants.find_descendants(SAMPLE_GRAPH, "www_app")
        assert result == []

    def test_returns_direct_descendants(self, dispatch_descendants) -> None:
        """Test that direct descendants are returned."""
        result = dispatch_descendants.find_descendants(SAMPLE_GRAPH, "bootstrap")
        assert set(result) == {"www_common", "api_common"}

    def test_returns_single_descendant(self, dispatch_descendants) -> None:
        """Test workflow with single descendant."""
        result = dispatch_descendants.find_descendants(SAMPLE_GRAPH, "www_common")
        assert result == ["www_app"]

    def test_returns_empty_for_unknown_workflow(self, dispatch_descendants) -> None:
        """Test that unknown workflow has no descendants."""
        result = dispatch_descendants.find_descendants(SAMPLE_GRAPH, "unknown")
        assert result == []


class TestGetWorkflowName:
    """Tests for get_workflow_name function."""

    def test_returns_name_from_graph(self, dispatch_descendants) -> None:
        """Test that workflow name is returned from graph."""
        result = dispatch_descendants.get_workflow_name(SAMPLE_GRAPH, "bootstrap")
        assert result == "Bootstrap"

    def test_returns_key_if_no_name(self, dispatch_descendants) -> None:
        """Test that workflow key is returned if no name in graph."""
        graph: dict = {"test": {"depends_on": []}}
        result = dispatch_descendants.get_workflow_name(graph, "test")
        assert result == "test"

    def test_returns_key_for_unknown_workflow(self, dispatch_descendants) -> None:
        """Test that workflow key is returned for unknown workflow."""
        result = dispatch_descendants.get_workflow_name(SAMPLE_GRAPH, "unknown")
        assert result == "unknown"


class TestCheckWorkflowCompleted:
    """Tests for check_workflow_completed function."""

    def test_returns_true_when_successful_run_exists(
        self, dispatch_descendants
    ) -> None:
        """Test returns True when a successful run exists."""
        mock_result = MagicMock()
        mock_result.stdout = "12345\n"
        since = datetime.now(timezone.utc)

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            result = dispatch_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is True

    def test_returns_false_when_no_successful_run(self, dispatch_descendants) -> None:
        """Test returns False when no successful run exists."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        since = datetime.now(timezone.utc)

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            result = dispatch_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is False

    def test_returns_false_when_only_whitespace(self, dispatch_descendants) -> None:
        """Test returns False when output is only whitespace."""
        mock_result = MagicMock()
        mock_result.stdout = "   \n"
        since = datetime.now(timezone.utc)

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            result = dispatch_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is False


class TestAllDependenciesMet:
    """Tests for all_dependencies_met function."""

    def test_single_dependency_returns_true(self, dispatch_descendants) -> None:
        """Test returns True when only current workflow is dependency."""
        graph: dict = {"child": {"depends_on": ["parent"]}}
        result, _ = dispatch_descendants.all_dependencies_met(
            graph, "child", "parent", "owner/repo", 24
        )
        assert result is True

    def test_single_dependency_returns_empty_missing(
        self, dispatch_descendants
    ) -> None:
        """Test returns empty missing list for single dependency."""
        graph: dict = {"child": {"depends_on": ["parent"]}}
        _, missing = dispatch_descendants.all_dependencies_met(
            graph, "child", "parent", "owner/repo", 24
        )
        assert missing == []

    def test_all_deps_completed_returns_true(self, dispatch_descendants) -> None:
        """Test returns True when all other dependencies have completed."""
        mock_result = MagicMock()
        mock_result.stdout = "12345\n"

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            result, _ = dispatch_descendants.all_dependencies_met(
                SAMPLE_GRAPH, "www_app", "www_common", "owner/repo", 24
            )
        assert result is True

    def test_all_deps_completed_returns_empty_missing(
        self, dispatch_descendants
    ) -> None:
        """Test returns empty missing when all deps completed."""
        mock_result = MagicMock()
        mock_result.stdout = "12345\n"

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            _, missing = dispatch_descendants.all_dependencies_met(
                SAMPLE_GRAPH, "www_app", "www_common", "owner/repo", 24
            )
        assert missing == []

    def test_missing_dep_returns_false(self, dispatch_descendants) -> None:
        """Test returns False when other dependency has not completed."""
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            result, _ = dispatch_descendants.all_dependencies_met(
                SAMPLE_GRAPH, "www_app", "www_common", "owner/repo", 24
            )
        assert result is False

    def test_missing_dep_returns_missing_workflow(self, dispatch_descendants) -> None:
        """Test returns missing workflow name when dep not completed."""
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("dispatch_descendants.subprocess.run", return_value=mock_result):
            _, missing = dispatch_descendants.all_dependencies_met(
                SAMPLE_GRAPH, "www_app", "www_common", "owner/repo", 24
            )
        assert missing == ["api_common"]


class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""

    def test_returns_true_on_success(self, dispatch_descendants) -> None:
        """Test returns True when dispatch succeeds."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ):
            result = dispatch_descendants.dispatch_workflow("test", "owner/repo")
        assert result is True

    def test_returns_false_on_failure(self, dispatch_descendants) -> None:
        """Test returns False when dispatch fails."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=False
        ):
            result = dispatch_descendants.dispatch_workflow("test", "owner/repo")
        assert result is False

    def test_trigger_descendants_includes_flag(self, dispatch_descendants) -> None:
        """Test that -f flag is included for trigger_descendants."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ) as mock:
            dispatch_descendants.dispatch_workflow(
                "test", "owner/repo", trigger_descendants=True
            )
        extra_args = mock.call_args[0][2]
        assert "-f" in extra_args

    def test_trigger_descendants_includes_value(self, dispatch_descendants) -> None:
        """Test that trigger_descendants=true value is included."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ) as mock:
            dispatch_descendants.dispatch_workflow(
                "test", "owner/repo", trigger_descendants=True
            )
        extra_args = mock.call_args[0][2]
        assert "trigger_descendants=true" in extra_args

    def test_invalidate_cloudfront_includes_flag(self, dispatch_descendants) -> None:
        """Test that -f flag is included for invalidate_cloudfront."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ) as mock:
            dispatch_descendants.dispatch_workflow(
                "test", "owner/repo", invalidate_cloudfront=True
            )
        extra_args = mock.call_args[0][2]
        assert "-f" in extra_args

    def test_invalidate_cloudfront_includes_value(self, dispatch_descendants) -> None:
        """Test that invalidate_cloudfront=true value is included."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ) as mock:
            dispatch_descendants.dispatch_workflow(
                "test", "owner/repo", invalidate_cloudfront=True
            )
        extra_args = mock.call_args[0][2]
        assert "invalidate_cloudfront=true" in extra_args

    def test_no_flags_when_both_false(self, dispatch_descendants) -> None:
        """Test that no flags are passed when both are False."""
        with patch(
            "dispatch_descendants.dispatch_gh_workflow", return_value=True
        ) as mock:
            dispatch_descendants.dispatch_workflow("test", "owner/repo")
        extra_args = mock.call_args[0][2]
        assert extra_args is None


class TestMain:
    """Tests for main function."""

    def test_returns_0_when_no_descendants(self, dispatch_descendants) -> None:
        """Test returns 0 when workflow has no descendants."""
        argv = ["prog", "--workflow", "www_app", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "dispatch_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
            ):
                result = dispatch_descendants.main()
        assert result == 0

    def test_returns_0_when_all_dispatches_succeed(
        self, dispatch_descendants
    ) -> None:
        """Test returns 0 when all dispatches succeed."""
        argv = ["prog", "--workflow", "bootstrap", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "dispatch_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
            ):
                with patch(
                    "dispatch_descendants.dispatch_workflow", return_value=True
                ):
                    result = dispatch_descendants.main()
        assert result == 0

    def test_returns_1_when_dispatch_fails(self, dispatch_descendants) -> None:
        """Test returns 1 when a dispatch fails."""
        argv = ["prog", "--workflow", "bootstrap", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "dispatch_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
            ):
                with patch(
                    "dispatch_descendants.dispatch_workflow", return_value=False
                ):
                    result = dispatch_descendants.main()
        assert result == 1

    def test_checks_all_dependencies_for_multi_dep_workflow(
        self, dispatch_descendants
    ) -> None:
        """Test that all_dependencies_met is called for multi-dependency workflow."""
        argv = ["prog", "--workflow", "www_common", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "dispatch_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
            ):
                with patch(
                    "dispatch_descendants.all_dependencies_met",
                    return_value=(True, [])
                ) as mock_deps:
                    with patch(
                        "dispatch_descendants.dispatch_workflow", return_value=True
                    ):
                        dispatch_descendants.main()
        mock_deps.assert_called_once()
        assert True  # Explicit pass

    def test_skips_dispatch_when_dependencies_not_met(
        self, dispatch_descendants
    ) -> None:
        """Test that dispatch is skipped when dependencies are not met."""
        _, mock_dispatch = _run_main_with_unmet_deps(dispatch_descendants)
        mock_dispatch.assert_not_called()
        assert True  # Explicit pass

    def test_returns_0_when_dependencies_not_met(self, dispatch_descendants) -> None:
        """Test returns 0 when skipping due to unmet dependencies."""
        result, _ = _run_main_with_unmet_deps(dispatch_descendants)
        assert result == 0

    def test_returns_1_when_dispatch_fails_with_met_deps(
        self, dispatch_descendants
    ) -> None:
        """Test returns 1 when dispatch fails for workflow with all deps met."""
        argv = ["prog", "--workflow", "www_common", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "dispatch_descendants.load_dependency_graph",
                return_value=SAMPLE_GRAPH
            ):
                with patch(
                    "dispatch_descendants.all_dependencies_met",
                    return_value=(True, [])
                ):
                    with patch(
                        "dispatch_descendants.dispatch_workflow",
                        return_value=False
                    ):
                        result = dispatch_descendants.main()
        assert result == 1
