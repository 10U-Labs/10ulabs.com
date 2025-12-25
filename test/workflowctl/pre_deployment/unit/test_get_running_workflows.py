"""Unit tests for get_running.py and utils.py."""

import json
from unittest.mock import MagicMock, patch

from utils import build_name_to_key_map, get_workflow_runs


# Sample dependency graph for testing
SAMPLE_GRAPH = {
    "bootstrap": {
        "name": "Ensuring bootstrap infrastructure exists and is properly configured",
        "depends_on": [],
        "paths": ["src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": ["src/www/shared/**"],
    },
    "api_backend": {
        "name": "Ensuring API backend exists and is properly configured",
        "depends_on": ["www_shared"],
        "paths": ["src/api/backend/**"],
    },
}


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_builds_correct_mapping(self) -> None:
        """Test that name-to-key mapping is built correctly."""
        name_to_key = build_name_to_key_map(SAMPLE_GRAPH)
        expected = {
            "Ensuring bootstrap infrastructure exists and is properly configured": "bootstrap",
            "WWW Shared": "www_shared",
            "Ensuring API backend exists and is properly configured": "api_backend",
        }
        assert name_to_key == expected

    def test_empty_graph(self) -> None:
        """Test with empty graph."""
        name_to_key = build_name_to_key_map({})
        assert not name_to_key

    def test_workflow_without_name(self) -> None:
        """Test workflow config without name field is skipped."""
        graph = {
            "no_name": {"depends_on": [], "paths": ["src/**"]},
            "with_name": {"name": "Named Workflow", "depends_on": []},
        }
        name_to_key = build_name_to_key_map(graph)
        assert name_to_key == {"Named Workflow": "with_name"}


class TestGetWorkflowRuns:
    """Tests for get_workflow_runs function."""

    @patch("utils.subprocess.run")
    def test_returns_runs_on_success(self, mock_run: MagicMock) -> None:
        """Test successful API response parsing."""
        runs = [
            {"id": 123, "name": "Bootstrap", "status": "in_progress"},
            {"id": 456, "name": "API", "status": "in_progress"},
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(runs),
            stderr=""
        )
        result = get_workflow_runs("owner/repo", "in_progress")
        assert result == runs

    @patch("utils.subprocess.run")
    def test_returns_empty_on_api_error(self, mock_run: MagicMock) -> None:
        """Test API error returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="API error"
        )
        result = get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_invalid_json(self, mock_run: MagicMock) -> None:
        """Test invalid JSON returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json",
            stderr=""
        )
        result = get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_empty_response(self, mock_run: MagicMock) -> None:
        """Test empty response returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = get_workflow_runs("owner/repo", "in_progress")
        assert result == []
