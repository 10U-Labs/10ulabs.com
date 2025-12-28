"""Unit tests for dispatch_workflow.py."""

import sys
from typing import Any, List, Optional
from unittest.mock import patch, MagicMock


def _run_main_with_input_flag(
    dispatch_workflow: Any,
    argv: List[str],
    accepts_input: bool
) -> Optional[List[str]]:
    """Run main() with input flag and return extra_args from dispatch call."""
    mock_dispatch = MagicMock(return_value=True)
    with patch.object(sys, "argv", argv):
        with patch("dispatch_workflow.workflow_file_exists", return_value=True):
            with patch("dispatch_workflow.workflow_accepts_input", return_value=accepts_input):
                with patch("dispatch_workflow.dispatch_gh_workflow", mock_dispatch):
                    dispatch_workflow.main()
    return mock_dispatch.call_args[0][2]


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parses_workflow_argument(self, dispatch_workflow) -> None:
        """Test that --workflow argument is parsed correctly."""
        with patch.object(sys, "argv", ["prog", "--workflow", "bootstrap", "--repo", "o/r"]):
            args = dispatch_workflow.parse_args()
        assert args.workflow == "bootstrap"

    def test_parses_repo_argument(self, dispatch_workflow) -> None:
        """Test that --repo argument is parsed correctly."""
        with patch.object(sys, "argv", ["prog", "--workflow", "test", "--repo", "owner/repo"]):
            args = dispatch_workflow.parse_args()
        assert args.repo == "owner/repo"

    def test_trigger_descendants_defaults_to_false(self, dispatch_workflow) -> None:
        """Test that --trigger-descendants defaults to False."""
        with patch.object(sys, "argv", ["prog", "--workflow", "test", "--repo", "o/r"]):
            args = dispatch_workflow.parse_args()
        assert args.trigger_descendants is False

    def test_trigger_descendants_true_when_flag_present(self, dispatch_workflow) -> None:
        """Test that --trigger-descendants sets flag to True."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--trigger-descendants"]
        with patch.object(sys, "argv", argv):
            args = dispatch_workflow.parse_args()
        assert args.trigger_descendants is True

    def test_invalidate_cloudfront_defaults_to_false(self, dispatch_workflow) -> None:
        """Test that --invalidate-cloudfront defaults to False."""
        with patch.object(sys, "argv", ["prog", "--workflow", "test", "--repo", "o/r"]):
            args = dispatch_workflow.parse_args()
        assert args.invalidate_cloudfront is False

    def test_invalidate_cloudfront_true_when_flag_present(self, dispatch_workflow) -> None:
        """Test that --invalidate-cloudfront sets flag to True."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--invalidate-cloudfront"]
        with patch.object(sys, "argv", argv):
            args = dispatch_workflow.parse_args()
        assert args.invalidate_cloudfront is True


class TestMain:
    """Tests for main function."""

    def test_returns_1_when_workflow_file_not_found(self, dispatch_workflow) -> None:
        """Test that main returns 1 when workflow file doesn't exist."""
        argv = ["prog", "--workflow", "nonexistent", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            with patch("dispatch_workflow.workflow_file_exists", return_value=False):
                result = dispatch_workflow.main()
        assert result == 1

    def test_returns_0_on_successful_dispatch(self, dispatch_workflow) -> None:
        """Test that main returns 0 when dispatch succeeds."""
        argv = ["prog", "--workflow", "test", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            with patch("dispatch_workflow.workflow_file_exists", return_value=True):
                with patch("dispatch_workflow.dispatch_gh_workflow", return_value=True):
                    result = dispatch_workflow.main()
        assert result == 0

    def test_returns_1_on_failed_dispatch(self, dispatch_workflow) -> None:
        """Test that main returns 1 when dispatch fails."""
        argv = ["prog", "--workflow", "test", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            with patch("dispatch_workflow.workflow_file_exists", return_value=True):
                with patch("dispatch_workflow.dispatch_gh_workflow", return_value=False):
                    result = dispatch_workflow.main()
        assert result == 1

    def test_trigger_descendants_includes_flag(self, dispatch_workflow) -> None:
        """Test that -f flag is included for trigger_descendants."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--trigger-descendants"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=True)
        assert extra_args is not None and "-f" in extra_args

    def test_trigger_descendants_includes_value(self, dispatch_workflow) -> None:
        """Test that trigger_descendants=true value is included."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--trigger-descendants"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=True)
        assert extra_args is not None and "trigger_descendants=true" in extra_args

    def test_skips_trigger_descendants_when_workflow_does_not_accept_it(
        self, dispatch_workflow
    ) -> None:
        """Test that trigger_descendants is not passed when workflow doesn't accept it."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--trigger-descendants"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=False)
        assert extra_args is None

    def test_invalidate_cloudfront_includes_flag(self, dispatch_workflow) -> None:
        """Test that -f flag is included for invalidate_cloudfront."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--invalidate-cloudfront"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=True)
        assert extra_args is not None and "-f" in extra_args

    def test_invalidate_cloudfront_includes_value(self, dispatch_workflow) -> None:
        """Test that invalidate_cloudfront=true value is included."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--invalidate-cloudfront"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=True)
        assert extra_args is not None and "invalidate_cloudfront=true" in extra_args

    def test_skips_invalidate_cloudfront_when_workflow_does_not_accept_it(
        self, dispatch_workflow
    ) -> None:
        """Test that invalidate_cloudfront is not passed when workflow doesn't accept it."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--invalidate-cloudfront"]
        extra_args = _run_main_with_input_flag(dispatch_workflow, argv, accepts_input=False)
        assert extra_args is None

    def test_calls_dispatch_with_correct_workflow_file(self, dispatch_workflow) -> None:
        """Test that dispatch is called with correct workflow file path."""
        argv = ["prog", "--workflow", "bootstrap", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            with patch("dispatch_workflow.workflow_file_exists", return_value=True):
                with patch("dispatch_workflow.dispatch_gh_workflow") as mock_dispatch:
                    mock_dispatch.return_value = True
                    dispatch_workflow.main()
        workflow_file = mock_dispatch.call_args[0][0]
        assert workflow_file == ".github/workflows/bootstrap.yml"

    def test_calls_dispatch_with_correct_repo(self, dispatch_workflow) -> None:
        """Test that dispatch is called with correct repo argument."""
        argv = ["prog", "--workflow", "test", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            with patch("dispatch_workflow.workflow_file_exists", return_value=True):
                with patch("dispatch_workflow.dispatch_gh_workflow") as mock_dispatch:
                    mock_dispatch.return_value = True
                    dispatch_workflow.main()
        repo = mock_dispatch.call_args[0][1]
        assert repo == "owner/repo"
