from pathlib import Path
import pytest

from repo_utils import (
    extract_brace_block,
    _find_repo_root,
    _find_repo_root_from_path,
    REPO_ROOT,
)


class TestFindRepoRoot:
    def test_returns_path(self) -> None:
        result = _find_repo_root()
        assert isinstance(result, Path)

    def test_returns_directory_with_git(self) -> None:
        result = _find_repo_root()
        assert (result / ".git").exists()

    def test_repo_root_constant_matches_function(self) -> None:
        assert REPO_ROOT == _find_repo_root()

    def test_raises_runtime_error_when_no_git_directory(self, tmp_path: Path) -> None:
        isolated_dir = tmp_path / "isolated" / "deep" / "path"
        isolated_dir.mkdir(parents=True)

        with pytest.raises(RuntimeError, match="Could not find repository root"):
            _find_repo_root_from_path(isolated_dir)


class TestExtractBraceBlock:
    def test_extracts_simple_block(self) -> None:
        content = 'before { content } after'
        result = extract_brace_block(content, 7)
        assert result == "{ content }"

    def test_extracts_nested_block(self) -> None:
        content = 'before { outer { inner } more } after'
        result = extract_brace_block(content, 7)
        assert result == "{ outer { inner } more }"

    def test_extracts_deeply_nested_block(self) -> None:
        content = 'start { a { b { c } b } a } end'
        result = extract_brace_block(content, 6)
        assert result == "{ a { b { c } b } a }"

    def test_unclosed_brace_returns_rest_of_content(self) -> None:
        content = 'before { unclosed content'
        result = extract_brace_block(content, 7)
        assert result == "{ unclosed content"

    def test_empty_block(self) -> None:
        content = 'before {} after'
        result = extract_brace_block(content, 7)
        assert result == "{}"

    def test_start_at_beginning(self) -> None:
        content = '{ content } after'
        result = extract_brace_block(content, 0)
        assert result == "{ content }"
