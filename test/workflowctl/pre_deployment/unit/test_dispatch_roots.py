"""Unit tests for dispatch_roots.py."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from dispatch_roots import (
    dispatch_workflow,
    should_trigger_descendants,
    workflow_accepts_trigger_descendants,
    workflow_file_exists,
)


class TestShouldTriggerDescendants:
    """Tests for should_trigger_descendants function."""

    def test_returns_true_when_input_is_true(self) -> None:
        """Test returns True when trigger_input is 'true'."""
        assert should_trigger_descendants("true", "", []) is True

    def test_returns_true_when_input_is_true_uppercase(self) -> None:
        """Test returns True when trigger_input is 'TRUE'."""
        assert should_trigger_descendants("TRUE", "", []) is True

    def test_returns_true_when_commit_has_tag(self) -> None:
        """Test returns True when commit message has [trigger descendants]."""
        assert should_trigger_descendants(
            "false",
            "feat: add feature [trigger descendants]",
            []
        ) is True

    def test_returns_true_when_commit_has_tag_case_insensitive(self) -> None:
        """Test [Trigger Descendants] tag is case insensitive."""
        assert should_trigger_descendants(
            "false",
            "feat: add feature [Trigger Descendants]",
            []
        ) is True

    def test_returns_true_when_dependencies_changed(self) -> None:
        """Test returns True when workflow-dependencies.json changed."""
        assert should_trigger_descendants(
            "false",
            "feat: update deps",
            ["etc/workflow-dependencies.json"]
        ) is True

    def test_returns_false_when_no_conditions_met(self) -> None:
        """Test returns False when no conditions are met."""
        assert should_trigger_descendants(
            "false",
            "feat: normal commit",
            ["src/file.py"]
        ) is False


class TestWorkflowFileExists:
    """Tests for workflow_file_exists function."""

    @patch("os.path.isfile")
    def test_returns_true_when_file_exists(self, mock_isfile: MagicMock) -> None:
        """Test returns True when workflow file exists."""
        mock_isfile.return_value = True
        assert workflow_file_exists("bootstrap") is True

    @patch("os.path.isfile")
    def test_checks_correct_path(self, mock_isfile: MagicMock) -> None:
        """Test checks correct workflow file path."""
        mock_isfile.return_value = True
        workflow_file_exists("bootstrap")
        mock_isfile.assert_called_once_with(".github/workflows/bootstrap.yml")

    @patch("os.path.isfile")
    def test_returns_false_when_file_missing(self, mock_isfile: MagicMock) -> None:
        """Test returns False when workflow file is missing."""
        mock_isfile.return_value = False
        assert workflow_file_exists("missing") is False


class TestWorkflowAcceptsTriggerDescendants:
    """Tests for workflow_accepts_trigger_descendants function."""

    def test_returns_true_when_input_present(self) -> None:
        """Test returns True when trigger_descendants input is defined."""
        content = """
name: Test Workflow
on:
  workflow_dispatch:
    inputs:
      trigger_descendants:
        default: false
        type: boolean
"""
        with patch("builtins.open", mock_open(read_data=content)):
            assert workflow_accepts_trigger_descendants("test") is True

    def test_returns_false_when_input_missing(self) -> None:
        """Test returns False when trigger_descendants input is not defined."""
        content = """
name: Test Workflow
on:
  workflow_dispatch:
    inputs:
      dry_run:
        default: false
        type: boolean
"""
        with patch("builtins.open", mock_open(read_data=content)):
            assert workflow_accepts_trigger_descendants("test") is False

    def test_returns_false_on_file_error(self) -> None:
        """Test returns False when file cannot be read."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            assert workflow_accepts_trigger_descendants("missing") is False


class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""

    def test_dry_run_returns_true(self) -> None:
        """Test dry run mode returns True."""
        with patch("dispatch_roots.dispatch_gh_workflow") as mock_dispatch:
            result = dispatch_workflow("test", "owner/repo", False, dry_run=True)
            assert result is True

    def test_dry_run_does_not_call_dispatch(self) -> None:
        """Test dry run mode doesn't call dispatch."""
        with patch("dispatch_roots.dispatch_gh_workflow") as mock_dispatch:
            dispatch_workflow("test", "owner/repo", False, dry_run=True)
            mock_dispatch.assert_not_called()

    @patch("dispatch_roots.workflow_accepts_trigger_descendants")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_returns_true_on_success(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock
    ) -> None:
        """Test dispatch returns True on success."""
        mock_dispatch.return_value = True
        result = dispatch_workflow("test", "owner/repo", False, dry_run=False)
        assert result is True

    @patch("dispatch_roots.workflow_accepts_trigger_descendants")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_without_flag_when_trigger_false(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock
    ) -> None:
        """Test dispatch passes None extra_args when trigger_descendants False."""
        mock_dispatch.return_value = True
        dispatch_workflow("test", "owner/repo", False, dry_run=False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] is None

    @patch("dispatch_roots.workflow_accepts_trigger_descendants")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_with_flag_when_workflow_accepts(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock
    ) -> None:
        """Test dispatch passes trigger_descendants flag when accepted."""
        mock_accepts.return_value = True
        mock_dispatch.return_value = True
        dispatch_workflow("test", "owner/repo", True, dry_run=False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] == ["-f", "trigger_descendants=true"]

    @patch("dispatch_roots.workflow_accepts_trigger_descendants")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_without_flag_when_workflow_rejects(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock
    ) -> None:
        """Test dispatch passes None when workflow rejects trigger_descendants."""
        mock_accepts.return_value = False
        mock_dispatch.return_value = True
        dispatch_workflow("test", "owner/repo", True, dry_run=False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] is None

    @patch("dispatch_roots.workflow_accepts_trigger_descendants")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_returns_false_on_dispatch_failure(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock
    ) -> None:
        """Test returns False when dispatch fails."""
        mock_dispatch.return_value = False
        result = dispatch_workflow("test", "owner/repo", False, dry_run=False)
        assert result is False
