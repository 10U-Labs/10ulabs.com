"""Unit tests for get_running.py and utils.py."""

import json
from unittest.mock import MagicMock, patch

from conftest import MINIMAL_GRAPH


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_builds_correct_mapping(self, utils) -> None:
        """Test that name-to-key mapping is built correctly."""
        name_to_key = utils.build_name_to_key_map(MINIMAL_GRAPH)
        expected = {
            "Ensuring bootstrap infrastructure exists and is properly configured": "bootstrap",
            "WWW Shared": "www_shared",
            "Ensuring API backend exists and is properly configured": "api_shared_routing",
        }
        assert name_to_key == expected

    def test_empty_graph(self, utils) -> None:
        """Test with empty graph."""
        name_to_key = utils.build_name_to_key_map({})
        assert not name_to_key

    def test_workflow_without_name(self, utils) -> None:
        """Test workflow config without name field is skipped."""
        graph = {
            "no_name": {"depends_on": [], "paths": ["src/**"]},
            "with_name": {"name": "Named Workflow", "depends_on": []},
        }
        name_to_key = utils.build_name_to_key_map(graph)
        assert name_to_key == {"Named Workflow": "with_name"}


class TestGetWorkflowRuns:
    """Tests for get_workflow_runs function."""

    @patch("utils.subprocess.run")
    def test_returns_runs_on_success(self, mock_run: MagicMock, utils) -> None:
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
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == runs

    @patch("utils.subprocess.run")
    def test_returns_empty_on_api_error(self, mock_run: MagicMock, utils) -> None:
        """Test API error returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="API error"
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_invalid_json(self, mock_run: MagicMock, utils) -> None:
        """Test invalid JSON returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json",
            stderr=""
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_empty_response(self, mock_run: MagicMock, utils) -> None:
        """Test empty response returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []
