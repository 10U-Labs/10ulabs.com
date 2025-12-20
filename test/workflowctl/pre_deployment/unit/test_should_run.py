"""Unit tests for should_run.py."""

import pytest

from should_run import (
    STATIC_ANALYSIS_PATTERNS,
    UNIT_TEST_PATTERNS,
    file_matches_pattern,
    should_run,
)


class TestFileMatchesPattern:
    """Tests for file_matches_pattern function."""

    def test_exact_match(self) -> None:
        """Test exact file path matching."""
        assert file_matches_pattern(
            ".github/workflows/workflowctl.yml",
            ".github/workflows/workflowctl.yml"
        )

    def test_exact_match_returns_false_for_different(self) -> None:
        """Test exact match returns False for different file."""
        assert not file_matches_pattern(
            ".github/workflows/other.yml",
            ".github/workflows/workflowctl.yml"
        )

    def test_glob_star_match(self) -> None:
        """Test single * glob pattern."""
        assert file_matches_pattern("src/workflowctl/cancel.py", "src/workflowctl/*.py")

    def test_glob_star_no_match(self) -> None:
        """Test single * glob pattern doesn't match different dir."""
        assert not file_matches_pattern("src/other/file.py", "src/workflowctl/*.py")

    def test_double_star_match_direct(self) -> None:
        """Test ** glob pattern matches direct child."""
        assert file_matches_pattern("test/workflowctl/test_file.py", "test/workflowctl/**")

    def test_double_star_match_nested(self) -> None:
        """Test ** glob pattern matches nested child."""
        assert file_matches_pattern(
            "test/workflowctl/pre_deployment/unit/test_file.py",
            "test/workflowctl/**"
        )

    def test_double_star_no_match(self) -> None:
        """Test ** glob pattern doesn't match different dir."""
        assert not file_matches_pattern("test/other/file.py", "test/workflowctl/**")


class TestShouldRun:
    """Tests for should_run function."""

    def test_returns_true_when_pattern_matches(self) -> None:
        """Test returns True when any file matches pattern."""
        changed = ["src/workflowctl/cancel.py"]
        patterns = ["src/workflowctl/*.py"]
        assert should_run(changed, patterns) is True

    def test_returns_false_when_no_match(self) -> None:
        """Test returns False when no files match."""
        changed = ["src/other/file.py"]
        patterns = ["src/workflowctl/*.py"]
        assert should_run(changed, patterns) is False

    def test_returns_true_for_any_matching_file(self) -> None:
        """Test returns True if any file matches."""
        changed = ["README.md", "src/workflowctl/cancel.py", "docs/guide.md"]
        patterns = ["src/workflowctl/*.py"]
        assert should_run(changed, patterns) is True

    def test_returns_true_for_any_matching_pattern(self) -> None:
        """Test returns True if file matches any pattern."""
        changed = [".github/workflows/workflowctl.yml"]
        patterns = ["src/workflowctl/*.py", ".github/workflows/workflowctl.yml"]
        assert should_run(changed, patterns) is True

    def test_empty_changed_files(self) -> None:
        """Test returns False for empty changed files."""
        assert should_run([], STATIC_ANALYSIS_PATTERNS) is False

    def test_empty_patterns(self) -> None:
        """Test returns False for empty patterns."""
        assert should_run(["file.py"], []) is False


class TestStaticAnalysisPatterns:
    """Tests for static analysis pattern matching."""

    def test_workflow_file_triggers(self) -> None:
        """Test that workflowctl.yml triggers static analysis."""
        assert should_run(
            [".github/workflows/workflowctl.yml"],
            STATIC_ANALYSIS_PATTERNS
        )

    def test_dependencies_json_triggers(self) -> None:
        """Test that workflow-dependencies.json triggers static analysis."""
        assert should_run(
            ["etc/workflow-dependencies.json"],
            STATIC_ANALYSIS_PATTERNS
        )

    def test_python_source_triggers(self) -> None:
        """Test that Python source files trigger static analysis."""
        assert should_run(
            ["src/workflowctl/cancel.py"],
            STATIC_ANALYSIS_PATTERNS
        )

    def test_unrelated_file_does_not_trigger(self) -> None:
        """Test that unrelated files don't trigger static analysis."""
        assert not should_run(
            ["README.md", "src/other/file.py"],
            STATIC_ANALYSIS_PATTERNS
        )


class TestUnitTestPatterns:
    """Tests for unit test pattern matching."""

    def test_workflow_file_triggers(self) -> None:
        """Test that workflowctl.yml triggers unit tests."""
        assert should_run(
            [".github/workflows/workflowctl.yml"],
            UNIT_TEST_PATTERNS
        )

    def test_python_source_triggers(self) -> None:
        """Test that Python source files trigger unit tests."""
        assert should_run(
            ["src/workflowctl/cancel.py"],
            UNIT_TEST_PATTERNS
        )

    def test_test_file_triggers(self) -> None:
        """Test that test files trigger unit tests."""
        assert should_run(
            ["test/workflowctl/pre_deployment/unit/test_file.py"],
            UNIT_TEST_PATTERNS
        )

    def test_dependencies_json_does_not_trigger(self) -> None:
        """Test that workflow-dependencies.json doesn't trigger unit tests."""
        assert not should_run(
            ["etc/workflow-dependencies.json"],
            UNIT_TEST_PATTERNS
        )
