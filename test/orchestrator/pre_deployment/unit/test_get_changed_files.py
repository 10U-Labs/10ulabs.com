"""Unit tests for get_changed_files.py."""

from unittest.mock import MagicMock, patch

import pytest

from get_changed_files import (
    ZERO_SHA,
    commit_exists,
    get_changed_files,
    get_changed_files_diff,
    get_changed_files_show,
)


class TestCommitExists:
    """Tests for commit_exists function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_true_when_commit_exists(self, mock_run: MagicMock) -> None:
        """Test that commit_exists returns True when commit exists."""
        mock_run.return_value = MagicMock(returncode=0)
        assert commit_exists("abc123") is True

    @patch("get_changed_files.run_subprocess")
    def test_returns_false_when_commit_missing(self, mock_run: MagicMock) -> None:
        """Test that commit_exists returns False when commit is missing."""
        mock_run.return_value = MagicMock(returncode=1)
        assert commit_exists("abc123") is False


class TestGetChangedFilesDiff:
    """Tests for get_changed_files_diff function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_files_on_success(self, mock_run: MagicMock) -> None:
        """Test successful git diff returns file list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\nfile3.py\n"
        )
        result = get_changed_files_diff("base", "head")
        assert result == ["file1.py", "file2.py", "file3.py"]

    @patch("get_changed_files.run_subprocess")
    def test_returns_empty_on_failure(self, mock_run: MagicMock) -> None:
        """Test failed git diff returns empty list."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_changed_files_diff("base", "head")
        assert result == []

    @patch("get_changed_files.run_subprocess")
    def test_filters_empty_lines(self, mock_run: MagicMock) -> None:
        """Test that empty lines are filtered out."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\n\nfile2.py\n"
        )
        result = get_changed_files_diff("base", "head")
        assert result == ["file1.py", "file2.py"]


class TestGetChangedFilesShow:
    """Tests for get_changed_files_show function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_files_on_success(self, mock_run: MagicMock) -> None:
        """Test successful git show returns file list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\n"
        )
        result = get_changed_files_show("head")
        assert result == ["file1.py", "file2.py"]

    @patch("get_changed_files.run_subprocess")
    def test_returns_empty_on_failure(self, mock_run: MagicMock) -> None:
        """Test failed git show returns empty list."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_changed_files_show("head")
        assert result == []


class TestGetChangedFiles:
    """Tests for get_changed_files function."""

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_head_minus_one_for_zero_sha(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock
    ) -> None:
        """Test that ZERO_SHA triggers HEAD~1 fallback."""
        mock_diff.return_value = ["file.py"]
        get_changed_files(ZERO_SHA, "head123")
        mock_diff.assert_called_once_with("HEAD~1", "head123")

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_base_when_commit_exists(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock
    ) -> None:
        """Test that existing base commit is used directly."""
        mock_exists.return_value = True
        mock_diff.return_value = ["file.py"]
        get_changed_files("base123", "head123")
        mock_diff.assert_called_once_with("base123", "head123")

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_head_minus_one_when_base_missing(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock
    ) -> None:
        """Test shallow clone fallback to HEAD~1."""
        mock_exists.return_value = False
        mock_diff.return_value = ["file.py"]
        get_changed_files("missing123", "head123")
        mock_diff.assert_called_once_with("HEAD~1", "head123")

    @patch("get_changed_files.get_changed_files_show")
    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_falls_back_to_show_when_diff_empty(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        mock_show: MagicMock
    ) -> None:
        """Test fallback to git show when diff returns empty."""
        mock_exists.return_value = True
        mock_diff.return_value = []
        mock_show.return_value = ["file.py"]
        result = get_changed_files("base123", "head123")
        assert result == ["file.py"]

    @patch("get_changed_files.get_changed_files_show")
    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_fallback_calls_show_with_head(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        mock_show: MagicMock
    ) -> None:
        """Test fallback calls git show with head commit."""
        mock_exists.return_value = True
        mock_diff.return_value = []
        mock_show.return_value = ["file.py"]
        get_changed_files("base123", "head123")
        mock_show.assert_called_once_with("head123")
