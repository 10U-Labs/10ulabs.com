"""Comprehensive tests for repo_utils module."""
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from repo_utils import (
    extract_brace_block,
    find_repo_root,
    _find_repo_root_from_path,
    REPO_ROOT,
)


class TestFindRepoRoot:
    """Tests for find_repo_root function."""

    def test_returns_path(self):
        """find_repo_root returns a Path object."""
        result = find_repo_root()
        assert isinstance(result, Path)

    def test_returns_directory_with_git(self):
        """find_repo_root returns a directory containing .git."""
        result = find_repo_root()
        assert (result / ".git").exists()

    def test_repo_root_constant_matches_function(self):
        """REPO_ROOT constant matches find_repo_root result."""
        assert REPO_ROOT == find_repo_root()

    def test_raises_runtime_error_when_no_git_directory(self, tmp_path):
        """Test RuntimeError when no .git directory found in any parent."""
        # Create a temporary directory structure with no .git
        # tmp_path itself and its parents don't have .git in the temp location
        isolated_dir = tmp_path / "isolated" / "deep" / "path"
        isolated_dir.mkdir(parents=True)

        # Use the actual function with a path that has no .git
        with pytest.raises(RuntimeError, match="Could not find repository root"):
            _find_repo_root_from_path(isolated_dir)


class TestExtractBraceBlock:
    """Tests for extract_brace_block function."""

    def test_extracts_simple_block(self):
        """extract_brace_block extracts a simple brace block."""
        content = 'before { content } after'
        result = extract_brace_block(content, 7)
        assert result == "{ content }"

    def test_extracts_nested_block(self):
        """extract_brace_block handles nested braces correctly."""
        content = 'before { outer { inner } more } after'
        result = extract_brace_block(content, 7)
        assert result == "{ outer { inner } more }"

    def test_extracts_deeply_nested_block(self):
        """extract_brace_block handles deeply nested braces."""
        content = 'start { a { b { c } b } a } end'
        result = extract_brace_block(content, 6)
        assert result == "{ a { b { c } b } a }"

    def test_unclosed_brace_returns_rest_of_content(self):
        """extract_brace_block returns remaining content when no closing brace."""
        content = 'before { unclosed content'
        result = extract_brace_block(content, 7)
        assert result == "{ unclosed content"

    def test_empty_block(self):
        """extract_brace_block handles empty blocks."""
        content = 'before {} after'
        result = extract_brace_block(content, 7)
        assert result == "{}"

    def test_start_at_beginning(self):
        """extract_brace_block works when block starts at beginning."""
        content = '{ content } after'
        result = extract_brace_block(content, 0)
        assert result == "{ content }"
