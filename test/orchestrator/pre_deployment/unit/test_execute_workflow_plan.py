"""Unit tests for execute_workflow_plan.py."""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from execute_workflow_plan import (
    dispatch_and_wait_single,
    execute_level,
    execute_plan,
    execute_plan_levels,
    get_latest_run_id,
    load_dependency_graph,
    run_gh,
    wait_for_completion,
)


# Sample dependency graph for testing
SAMPLE_GRAPH = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
    },
    "api": {
        "name": "API Backend",
        "depends_on": ["www_shared"],
    },
}


class TestRunGh:
    """Tests for run_gh function."""

    def test_run_gh_success(self) -> None:
        """Test successful gh command execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "version"],
                returncode=0,
                stdout="gh version 2.0.0\n",
                stderr="",
            )
            result = run_gh("version")
            assert result.returncode == 0
            assert "gh version" in result.stdout
            mock_run.assert_called_once_with(
                ["gh", "version"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_run_gh_with_multiple_args(self) -> None:
        """Test gh command with multiple arguments."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "run", "list", "--limit", "1"],
                returncode=0,
                stdout="",
                stderr="",
            )
            run_gh("run", "list", "--limit", "1")
            mock_run.assert_called_once_with(
                ["gh", "run", "list", "--limit", "1"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_run_gh_failure(self) -> None:
        """Test failed gh command execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "invalid"],
                returncode=1,
                stdout="",
                stderr="unknown command",
            )
            result = run_gh("invalid")
            assert result.returncode == 1
            assert "unknown command" in result.stderr


class TestGetLatestRunId:
    """Tests for get_latest_run_id function."""

    def test_get_latest_run_id_success(self) -> None:
        """Test successful run ID retrieval."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="12345678\n",
                stderr="",
            )
            run_id = get_latest_run_id("bootstrap.yml")
            assert run_id == "12345678"
            mock_run_gh.assert_called_once_with(
                "run", "list",
                "--workflow", "bootstrap.yml",
                "--limit", "1",
                "--json", "databaseId",
                "--jq", ".[0].databaseId",
            )

    def test_get_latest_run_id_no_runs(self) -> None:
        """Test when no runs exist."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )
            run_id = get_latest_run_id("bootstrap.yml")
            assert run_id is None

    def test_get_latest_run_id_failure(self) -> None:
        """Test when gh command fails."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="error",
            )
            run_id = get_latest_run_id("bootstrap.yml")
            assert run_id is None


class TestWaitForCompletion:
    """Tests for wait_for_completion function."""

    def test_wait_for_completion_success(self) -> None:
        """Test waiting for successful workflow completion."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="completed\tsuccess\n",
                stderr="",
            )
            success, conclusion = wait_for_completion("12345", "test")
            assert success is True
            assert conclusion == "success"

    def test_wait_for_completion_failure(self) -> None:
        """Test waiting for failed workflow completion."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="completed\tfailure\n",
                stderr="",
            )
            success, conclusion = wait_for_completion("12345", "test")
            assert success is False
            assert conclusion == "failure"

    def test_wait_for_completion_in_progress_then_success(self) -> None:
        """Test waiting while workflow is in progress then completes."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("time.sleep"):  # Skip actual sleeping
                mock_run_gh.side_effect = [
                    subprocess.CompletedProcess(
                        args=[], returncode=0,
                        stdout="in_progress\t\n", stderr="",
                    ),
                    subprocess.CompletedProcess(
                        args=[], returncode=0,
                        stdout="completed\tsuccess\n", stderr="",
                    ),
                ]
                success, conclusion = wait_for_completion("12345", "test")
                assert success is True
                assert conclusion == "success"

    def test_wait_for_completion_timeout(self) -> None:
        """Test timeout while waiting for completion."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("time.sleep"):
                with patch("time.time") as mock_time:
                    # Simulate time passing beyond timeout
                    mock_time.side_effect = [0, 0, 4000]
                    mock_run_gh.return_value = subprocess.CompletedProcess(
                        args=[], returncode=0,
                        stdout="in_progress\t\n", stderr="",
                    )
                    success, conclusion = wait_for_completion(
                        "12345", "test", timeout_minutes=1
                    )
                    assert success is False
                    assert conclusion == "timeout"


class TestLoadDependencyGraph:
    """Tests for load_dependency_graph function."""

    def test_load_dependency_graph(self) -> None:
        """Test loading dependency graph from YAML file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as tmp:
            yaml.dump(SAMPLE_GRAPH, tmp)
            tmp.flush()

            graph = load_dependency_graph(Path(tmp.name))
            assert graph == SAMPLE_GRAPH


class TestDispatchAndWaitSingle:
    """Tests for dispatch_and_wait_single function."""

    def test_dispatch_and_wait_success(self) -> None:
        """Test successful workflow dispatch and completion."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.return_value = (True, "success")

                        wf_key, success, conclusion = dispatch_and_wait_single(
                            "bootstrap", SAMPLE_GRAPH
                        )

                        assert wf_key == "bootstrap"
                        assert success is True
                        assert conclusion == "success"

    def test_dispatch_failure(self) -> None:
        """Test workflow dispatch failure."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="dispatch error",
            )

            wf_key, success, conclusion = dispatch_and_wait_single(
                "bootstrap", SAMPLE_GRAPH
            )

            assert wf_key == "bootstrap"
            assert success is False
            assert conclusion == "dispatch_failed"

    def test_dispatch_no_run_id(self) -> None:
        """Test when run ID cannot be found after dispatch."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch("time.sleep"):
                    mock_run_gh.return_value = subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="", stderr="",
                    )
                    mock_get_id.return_value = None

                    wf_key, success, conclusion = dispatch_and_wait_single(
                        "bootstrap", SAMPLE_GRAPH
                    )

                    assert wf_key == "bootstrap"
                    assert success is False
                    assert conclusion == "no_run_id"

    def test_dispatch_with_github_hosted(self) -> None:
        """Test dispatch with github_hosted flag."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.return_value = (True, "success")

                        dispatch_and_wait_single(
                            "bootstrap", SAMPLE_GRAPH, github_hosted=True
                        )

                        # Verify --field github_hosted=true was passed
                        call_args = mock_run_gh.call_args[0]
                        assert "--field" in call_args
                        assert "github_hosted=true" in call_args

    def test_dispatch_ecs_on_demand_no_github_hosted(self) -> None:
        """Test ECS on-demand workflows don't get github_hosted flag."""
        ecs_graph = {
            "contact": {
                "name": "Contact",
                "depends_on": [],
            },
        }
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.return_value = (True, "success")

                        dispatch_and_wait_single(
                            "contact", ecs_graph, github_hosted=True
                        )

                        # Verify --field github_hosted=true was NOT passed
                        call_args = mock_run_gh.call_args[0]
                        assert "github_hosted=true" not in call_args


class TestExecuteLevel:
    """Tests for execute_level function."""

    def test_execute_level_single_workflow(self) -> None:
        """Test executing level with single workflow."""
        with patch(
            "execute_workflow_plan.dispatch_and_wait_single"
        ) as mock_dispatch:
            mock_dispatch.return_value = ("bootstrap", True, "success")

            failed = execute_level(["bootstrap"], SAMPLE_GRAPH)

            assert failed == []
            mock_dispatch.assert_called_once()

    def test_execute_level_single_workflow_failure(self) -> None:
        """Test executing level with single failing workflow."""
        with patch(
            "execute_workflow_plan.dispatch_and_wait_single"
        ) as mock_dispatch:
            mock_dispatch.return_value = ("bootstrap", False, "failure")

            failed = execute_level(["bootstrap"], SAMPLE_GRAPH)

            assert failed == ["bootstrap"]

    def test_execute_level_parallel_all_success(self) -> None:
        """Test executing level with parallel workflows, all succeed."""
        with patch(
            "execute_workflow_plan.dispatch_and_wait_single"
        ) as mock_dispatch:
            mock_dispatch.side_effect = [
                ("bootstrap", True, "success"),
                ("www_shared", True, "success"),
            ]

            failed = execute_level(["bootstrap", "www_shared"], SAMPLE_GRAPH)

            assert failed == []
            assert mock_dispatch.call_count == 2

    def test_execute_level_parallel_one_failure(self) -> None:
        """Test executing level with parallel workflows, one fails."""
        with patch(
            "execute_workflow_plan.dispatch_and_wait_single"
        ) as mock_dispatch:
            mock_dispatch.side_effect = [
                ("bootstrap", True, "success"),
                ("www_shared", False, "failure"),
            ]

            failed = execute_level(["bootstrap", "www_shared"], SAMPLE_GRAPH)

            assert "www_shared" in failed
            assert "bootstrap" not in failed


class TestExecutePlanLevels:
    """Tests for execute_plan_levels function."""

    def test_execute_plan_levels_single_level(self) -> None:
        """Test executing plan with single level."""
        with patch("execute_workflow_plan.execute_level") as mock_execute:
            mock_execute.return_value = []

            failed = execute_plan_levels([["bootstrap"]], SAMPLE_GRAPH)

            assert failed == []
            mock_execute.assert_called_once_with(
                ["bootstrap"], SAMPLE_GRAPH, False
            )

    def test_execute_plan_levels_multiple_levels(self) -> None:
        """Test executing plan with multiple levels."""
        with patch("execute_workflow_plan.execute_level") as mock_execute:
            mock_execute.return_value = []

            levels = [["bootstrap"], ["www_shared"], ["api"]]
            failed = execute_plan_levels(levels, SAMPLE_GRAPH)

            assert failed == []
            assert mock_execute.call_count == 3

    def test_execute_plan_levels_stops_on_failure(self) -> None:
        """Test that execution stops when a level fails."""
        with patch("execute_workflow_plan.execute_level") as mock_execute:
            mock_execute.side_effect = [
                [],  # Level 0 succeeds
                ["www_shared"],  # Level 1 fails
            ]

            levels = [["bootstrap"], ["www_shared"], ["api"]]
            failed = execute_plan_levels(levels, SAMPLE_GRAPH)

            assert failed == ["www_shared"]
            # Should only call twice, stopping after level 1 failure
            assert mock_execute.call_count == 2

    def test_execute_plan_levels_with_github_hosted(self) -> None:
        """Test executing plan with github_hosted flag."""
        with patch("execute_workflow_plan.execute_level") as mock_execute:
            mock_execute.return_value = []

            execute_plan_levels([["bootstrap"]], SAMPLE_GRAPH, github_hosted=True)

            mock_execute.assert_called_once_with(
                ["bootstrap"], SAMPLE_GRAPH, True
            )


class TestExecutePlan:
    """Tests for execute_plan function (sequential execution)."""

    def test_execute_plan_success(self) -> None:
        """Test successful sequential execution."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.return_value = (True, "success")

                        failed = execute_plan(
                            ["bootstrap", "www_shared"], SAMPLE_GRAPH
                        )

                        assert failed == []

    def test_execute_plan_stops_on_failure(self) -> None:
        """Test that sequential execution stops on first failure."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.side_effect = [
                            (True, "success"),
                            (False, "failure"),
                        ]

                        failed = execute_plan(
                            ["bootstrap", "www_shared", "api"], SAMPLE_GRAPH
                        )

                        assert failed == ["www_shared"]
                        # Should have called wait twice (bootstrap success,
                        # www_shared failure, then stop)
                        assert mock_wait.call_count == 2

    def test_execute_plan_dispatch_failure(self) -> None:
        """Test handling dispatch failure in sequential execution."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            mock_run_gh.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="error",
            )

            failed = execute_plan(["bootstrap"], SAMPLE_GRAPH)

            assert failed == ["bootstrap"]

    def test_execute_plan_with_github_hosted(self) -> None:
        """Test sequential execution with github_hosted flag."""
        with patch("execute_workflow_plan.run_gh") as mock_run_gh:
            with patch("execute_workflow_plan.get_latest_run_id") as mock_get_id:
                with patch(
                    "execute_workflow_plan.wait_for_completion"
                ) as mock_wait:
                    with patch("time.sleep"):
                        mock_run_gh.return_value = subprocess.CompletedProcess(
                            args=[], returncode=0, stdout="", stderr="",
                        )
                        mock_get_id.return_value = "12345"
                        mock_wait.return_value = (True, "success")

                        execute_plan(
                            ["bootstrap"], SAMPLE_GRAPH, github_hosted=True
                        )

                        # Verify --field github_hosted=true was passed
                        call_args = mock_run_gh.call_args[0]
                        assert "--field" in call_args
                        assert "github_hosted=true" in call_args
