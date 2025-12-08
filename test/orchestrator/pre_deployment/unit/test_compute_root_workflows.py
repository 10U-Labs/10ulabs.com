"""Unit tests for compute_root_workflows.py."""

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from compute_root_workflows import (
    _insert_sorted,
    _output_results,
    _output_slots,
    compute_execution_plan,
    compute_execution_plan_levels,
    compute_root_workflows,
    file_matches_patterns,
    get_affected_workflows,
    get_all_ancestors,
    get_all_descendants,
    topological_sort,
    topological_sort_levels,
)


# Sample dependency graph for testing
SAMPLE_GRAPH = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_shared.yml", "src/www/shared/**"],
    },
    "api": {
        "name": "API",
        "depends_on": ["www_shared"],
        "paths": [".github/workflows/api_backend.yml", "src/api/backend/**"],
    },
    "health": {
        "name": "Health",
        "depends_on": ["api"],
        "paths": [".github/workflows/endpoint_health.yml", "src/api/endpoints/health/**"],
    },
    "ecr": {
        "name": "ECR",
        "depends_on": ["health"],
        "paths": [".github/workflows/api_shared_ecr.yml", "src/api/shared/ecr/**"],
    },
    "image_for_ecs_runners": {
        "name": "Image for ECS Runners",
        "depends_on": ["ecr"],
        "paths": [
            ".github/workflows/endpoint_v1_image_for_ecs_runners.yml",
            "src/api/endpoints/image_for_ecs_runners/**",
        ],
    },
    "ecs_runner": {
        "name": "ECS Runner",
        "depends_on": ["image_for_ecs_runners"],
        "paths": [
            ".github/workflows/endpoint_v1_ecs_runner.yml",
            "src/api/endpoints/ecs_runner/**",
        ],
    },
    "contact": {
        "name": "Contact",
        "depends_on": ["ecs_runner"],
        "paths": [".github/workflows/endpoint_v1_contact.yml", "src/api/endpoints/contact/**"],
    },
}


class TestFileMatchesPatterns:
    """Tests for file_matches_patterns function."""

    def test_exact_match(self) -> None:
        """Test exact file path matching."""
        patterns = [".github/workflows/bootstrap.yml"]
        assert file_matches_patterns(".github/workflows/bootstrap.yml", patterns)
        assert not file_matches_patterns(".github/workflows/api_backend.yml", patterns)

    def test_glob_star_match(self) -> None:
        """Test single * glob pattern matching.

        Note: fnmatch treats * as matching any characters including /,
        so src/*.tf matches src/sub/main.tf. This is acceptable since
        we primarily use ** patterns in workflow-dependencies.yml.
        """
        patterns = ["src/*.tf"]
        assert file_matches_patterns("src/main.tf", patterns)
        # fnmatch * matches any chars including /, so this also matches
        assert file_matches_patterns("src/sub/main.tf", patterns)

    def test_double_star_match(self) -> None:
        """Test ** glob pattern matching."""
        patterns = ["src/bootstrap/**"]
        assert file_matches_patterns("src/bootstrap/main.tf", patterns)
        assert file_matches_patterns("src/bootstrap/sub/file.tf", patterns)
        assert not file_matches_patterns("src/api/main.tf", patterns)

    def test_multiple_patterns(self) -> None:
        """Test matching against multiple patterns."""
        patterns = [".github/workflows/bootstrap.yml", "src/bootstrap/**"]
        assert file_matches_patterns(".github/workflows/bootstrap.yml", patterns)
        assert file_matches_patterns("src/bootstrap/main.tf", patterns)
        assert not file_matches_patterns("src/api/main.tf", patterns)

    def test_empty_patterns(self) -> None:
        """Test with empty pattern list."""
        assert not file_matches_patterns("any/file.txt", [])


class TestGetAllAncestors:
    """Tests for get_all_ancestors function."""

    def test_no_ancestors(self) -> None:
        """Test workflow with no dependencies."""
        ancestors = get_all_ancestors("bootstrap", SAMPLE_GRAPH)
        assert ancestors == set()

    def test_single_ancestor(self) -> None:
        """Test workflow with one direct dependency."""
        ancestors = get_all_ancestors("www_shared", SAMPLE_GRAPH)
        assert ancestors == {"bootstrap"}

    def test_transitive_ancestors(self) -> None:
        """Test workflow with transitive dependencies."""
        ancestors = get_all_ancestors("api", SAMPLE_GRAPH)
        assert ancestors == {"bootstrap", "www_shared"}

    def test_deep_ancestors(self) -> None:
        """Test workflow deep in the dependency chain."""
        ancestors = get_all_ancestors("contact", SAMPLE_GRAPH)
        expected = {
            "bootstrap",
            "www_shared",
            "api",
            "health",
            "ecr",
            "image_for_ecs_runners",
            "ecs_runner",
        }
        assert ancestors == expected

    def test_caching(self) -> None:
        """Test that ancestor computation uses caching."""
        cache: dict[str, set[str]] = {}
        get_all_ancestors("api", SAMPLE_GRAPH, cache)
        assert "api" in cache
        assert "www_shared" in cache
        assert "bootstrap" in cache


class TestGetAffectedWorkflows:
    """Tests for get_affected_workflows function."""

    def test_single_file_single_workflow(self) -> None:
        """Test single file affecting single workflow."""
        changed = ["src/bootstrap/main.tf"]
        affected = get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap"}

    def test_single_file_workflow_file(self) -> None:
        """Test changing a workflow file itself."""
        changed = [".github/workflows/api_backend.yml"]
        affected = get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"api"}

    def test_multiple_files_single_workflow(self) -> None:
        """Test multiple files affecting single workflow."""
        changed = ["src/bootstrap/main.tf", "src/bootstrap/variables.tf"]
        affected = get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap"}

    def test_multiple_files_multiple_workflows(self) -> None:
        """Test files affecting multiple workflows."""
        changed = ["src/bootstrap/main.tf", "src/api/backend/main.tf"]
        affected = get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap", "api"}

    def test_no_matching_files(self) -> None:
        """Test with files that don't match any workflow."""
        changed = ["README.md", "docs/guide.md"]
        affected = get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == set()


class TestComputeRootWorkflows:
    """Tests for compute_root_workflows function."""

    def test_single_root_workflow(self) -> None:
        """Test single workflow change returns that workflow as root."""
        changed = ["src/bootstrap/main.tf"]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["bootstrap"]

    def test_ancestor_and_descendant_changed(self) -> None:
        """Test that only ancestor is returned when both are changed."""
        changed = ["src/bootstrap/main.tf", "src/www/shared/main.tf"]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        # Only bootstrap should be root; www_shared will cascade
        assert roots == ["bootstrap"]

    def test_deep_chain_only_root(self) -> None:
        """Test deep chain returns only the root."""
        changed = [
            "src/bootstrap/main.tf",
            "src/www/shared/main.tf",
            "src/api/backend/main.tf",
            "src/api/endpoints/health/main.tf",
        ]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["bootstrap"]

    def test_independent_workflows(self) -> None:
        """Test multiple independent workflow changes."""
        # Create a graph with two independent branches
        graph = {
            "a": {"depends_on": [], "paths": ["src/a/**"]},
            "b": {"depends_on": [], "paths": ["src/b/**"]},
            "c": {"depends_on": ["a"], "paths": ["src/c/**"]},
            "d": {"depends_on": ["b"], "paths": ["src/d/**"]},
        }
        changed = ["src/a/file.tf", "src/b/file.tf"]
        roots = compute_root_workflows(changed, graph)
        assert sorted(roots) == ["a", "b"]

    def test_middle_of_chain(self) -> None:
        """Test changing middle of chain returns that workflow as root."""
        changed = ["src/api/backend/main.tf"]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["api"]

    def test_no_changes(self) -> None:
        """Test empty file list returns empty roots."""
        roots = compute_root_workflows([], SAMPLE_GRAPH)
        assert roots == []

    def test_unrelated_files(self) -> None:
        """Test files not matching any workflow return empty roots."""
        changed = ["README.md"]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == []

    def test_leaf_workflow_only(self) -> None:
        """Test changing only a leaf workflow returns it as root."""
        changed = ["src/api/endpoints/contact/main.tf"]
        roots = compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["contact"]


class TestDiamondDependency:
    """Tests for diamond dependency patterns (multiple paths to same node)."""

    @pytest.fixture
    def diamond_graph(self) -> dict:
        """Create a diamond-shaped dependency graph."""
        return {
            "root": {"depends_on": [], "paths": ["src/root/**"]},
            "left": {"depends_on": ["root"], "paths": ["src/left/**"]},
            "right": {"depends_on": ["root"], "paths": ["src/right/**"]},
            "bottom": {"depends_on": ["left", "right"], "paths": ["src/bottom/**"]},
        }

    def test_diamond_root_change(self, diamond_graph: dict) -> None:
        """Test changing root in diamond returns only root."""
        changed = ["src/root/file.tf"]
        roots = compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]

    def test_diamond_both_middle(self, diamond_graph: dict) -> None:
        """Test changing both middle nodes returns both as roots."""
        changed = ["src/left/file.tf", "src/right/file.tf"]
        roots = compute_root_workflows(changed, diamond_graph)
        assert sorted(roots) == ["left", "right"]

    def test_diamond_one_middle_and_bottom(self, diamond_graph: dict) -> None:
        """Test changing one middle and bottom returns only middle."""
        changed = ["src/left/file.tf", "src/bottom/file.tf"]
        roots = compute_root_workflows(changed, diamond_graph)
        # Only left is root; bottom has left as ancestor
        assert roots == ["left"]

    def test_diamond_all_nodes(self, diamond_graph: dict) -> None:
        """Test changing all nodes returns only root."""
        changed = [
            "src/root/file.tf",
            "src/left/file.tf",
            "src/right/file.tf",
            "src/bottom/file.tf",
        ]
        roots = compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_no_descendants(self) -> None:
        """Test leaf workflow with no dependents."""
        descendants = get_all_descendants("contact", SAMPLE_GRAPH)
        assert descendants == set()

    def test_single_descendant(self) -> None:
        """Test workflow with one direct dependent."""
        descendants = get_all_descendants("ecs_runner", SAMPLE_GRAPH)
        assert descendants == {"contact"}

    def test_transitive_descendants(self) -> None:
        """Test workflow with transitive dependents."""
        descendants = get_all_descendants("ecr", SAMPLE_GRAPH)
        assert descendants == {"image_for_ecs_runners", "ecs_runner", "contact"}

    def test_root_descendants(self) -> None:
        """Test root workflow has all others as descendants."""
        descendants = get_all_descendants("bootstrap", SAMPLE_GRAPH)
        expected = {
            "www_shared",
            "api",
            "health",
            "ecr",
            "image_for_ecs_runners",
            "ecs_runner",
            "contact",
        }
        assert descendants == expected

    def test_caching(self) -> None:
        """Test that descendant computation uses caching."""
        cache: dict[str, set[str]] = {}
        get_all_descendants("ecr", SAMPLE_GRAPH, cache)
        assert "ecr" in cache
        assert "image_for_ecs_runners" in cache
        assert "ecs_runner" in cache
        assert "contact" in cache


class TestInsertSorted:
    """Tests for _insert_sorted function."""

    def test_insert_into_empty_list(self) -> None:
        """Test inserting into empty list."""
        queue: list[str] = []
        _insert_sorted(queue, "b")
        assert queue == ["b"]

    def test_insert_at_beginning(self) -> None:
        """Test inserting at beginning of list."""
        queue = ["c", "d", "e"]
        _insert_sorted(queue, "a")
        assert queue == ["a", "c", "d", "e"]

    def test_insert_at_end(self) -> None:
        """Test inserting at end of list."""
        queue = ["a", "b", "c"]
        _insert_sorted(queue, "z")
        assert queue == ["a", "b", "c", "z"]

    def test_insert_in_middle(self) -> None:
        """Test inserting in middle of list."""
        queue = ["a", "c", "e"]
        _insert_sorted(queue, "b")
        assert queue == ["a", "b", "c", "e"]

    def test_insert_duplicate(self) -> None:
        """Test inserting duplicate value."""
        queue = ["a", "c", "e"]
        _insert_sorted(queue, "c")
        assert queue == ["a", "c", "c", "e"]


class TestTopologicalSort:
    """Tests for topological_sort function."""

    def test_single_workflow(self) -> None:
        """Test sorting single workflow."""
        workflows = {"bootstrap"}
        result = topological_sort(workflows, SAMPLE_GRAPH)
        assert result == ["bootstrap"]

    def test_linear_chain(self) -> None:
        """Test sorting linear dependency chain."""
        workflows = {"bootstrap", "www_shared", "api"}
        result = topological_sort(workflows, SAMPLE_GRAPH)
        assert result == ["bootstrap", "www_shared", "api"]

    def test_respects_dependencies(self) -> None:
        """Test that dependencies come before dependents."""
        workflows = {"api", "bootstrap", "www_shared", "health"}
        result = topological_sort(workflows, SAMPLE_GRAPH)
        # Verify order: bootstrap before www_shared before api before health
        assert result.index("bootstrap") < result.index("www_shared")
        assert result.index("www_shared") < result.index("api")
        assert result.index("api") < result.index("health")

    def test_diamond_pattern(self) -> None:
        """Test sorting diamond-shaped graph."""
        graph = {
            "root": {"depends_on": []},
            "left": {"depends_on": ["root"]},
            "right": {"depends_on": ["root"]},
            "bottom": {"depends_on": ["left", "right"]},
        }
        workflows = {"root", "left", "right", "bottom"}
        result = topological_sort(workflows, graph)
        # Root must be first, bottom must be last
        assert result[0] == "root"
        assert result[-1] == "bottom"
        # Left and right must be before bottom
        assert result.index("left") < result.index("bottom")
        assert result.index("right") < result.index("bottom")

    def test_partial_graph(self) -> None:
        """Test sorting subset of graph."""
        workflows = {"api", "health"}
        result = topological_sort(workflows, SAMPLE_GRAPH)
        # api must come before health
        assert result == ["api", "health"]


class TestTopologicalSortLevels:
    """Tests for topological_sort_levels function."""

    def test_single_workflow(self) -> None:
        """Test single workflow returns single level."""
        workflows = {"bootstrap"}
        levels = topological_sort_levels(workflows, SAMPLE_GRAPH)
        assert levels == [["bootstrap"]]

    def test_linear_chain(self) -> None:
        """Test linear chain returns one workflow per level."""
        workflows = {"bootstrap", "www_shared", "api"}
        levels = topological_sort_levels(workflows, SAMPLE_GRAPH)
        assert levels == [["bootstrap"], ["www_shared"], ["api"]]

    def test_parallel_workflows(self) -> None:
        """Test parallel workflows in same level."""
        graph = {
            "root": {"depends_on": []},
            "left": {"depends_on": ["root"]},
            "right": {"depends_on": ["root"]},
            "bottom": {"depends_on": ["left", "right"]},
        }
        workflows = {"root", "left", "right", "bottom"}
        levels = topological_sort_levels(workflows, graph)
        assert len(levels) == 3
        assert levels[0] == ["root"]
        assert sorted(levels[1]) == ["left", "right"]
        assert levels[2] == ["bottom"]

    def test_complex_parallel(self) -> None:
        """Test complex graph with multiple parallel paths."""
        graph = {
            "a": {"depends_on": []},
            "b": {"depends_on": ["a"]},
            "c": {"depends_on": ["a"]},
            "d": {"depends_on": ["b"]},
            "e": {"depends_on": ["c"]},
            "f": {"depends_on": ["d", "e"]},
        }
        workflows = {"a", "b", "c", "d", "e", "f"}
        levels = topological_sort_levels(workflows, graph)
        assert len(levels) == 4
        assert levels[0] == ["a"]
        assert sorted(levels[1]) == ["b", "c"]
        assert sorted(levels[2]) == ["d", "e"]
        assert levels[3] == ["f"]


class TestComputeExecutionPlan:
    """Tests for compute_execution_plan function."""

    def test_single_root_no_descendants(self) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        plan = compute_execution_plan(["a"], graph)
        assert plan == ["a"]

    def test_single_root_with_descendants(self) -> None:
        """Test single root includes all descendants."""
        plan = compute_execution_plan(["bootstrap"], SAMPLE_GRAPH)
        expected = [
            "bootstrap",
            "www_shared",
            "api",
            "health",
            "ecr",
            "image_for_ecs_runners",
            "ecs_runner",
            "contact",
        ]
        assert plan == expected

    def test_middle_root(self) -> None:
        """Test starting from middle of chain."""
        plan = compute_execution_plan(["ecr"], SAMPLE_GRAPH)
        expected = ["ecr", "image_for_ecs_runners", "ecs_runner", "contact"]
        assert plan == expected

    def test_multiple_roots(self) -> None:
        """Test multiple roots combine descendants."""
        graph = {
            "a": {"depends_on": []},
            "b": {"depends_on": []},
            "c": {"depends_on": ["a"]},
            "d": {"depends_on": ["b"]},
        }
        plan = compute_execution_plan(["a", "b"], graph)
        # Both branches included
        assert set(plan) == {"a", "b", "c", "d"}
        # Order respects dependencies
        assert plan.index("a") < plan.index("c")
        assert plan.index("b") < plan.index("d")


class TestComputeExecutionPlanLevels:
    """Tests for compute_execution_plan_levels function."""

    def test_single_root_no_descendants(self) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        levels = compute_execution_plan_levels(["a"], graph)
        assert levels == [["a"]]

    def test_single_root_with_descendants(self) -> None:
        """Test single root includes all descendants in levels."""
        levels = compute_execution_plan_levels(["bootstrap"], SAMPLE_GRAPH)
        # Should be 8 levels for linear chain
        assert len(levels) == 8
        assert levels[0] == ["bootstrap"]
        assert levels[-1] == ["contact"]

    def test_parallel_branches(self) -> None:
        """Test parallel branches appear in same level."""
        graph = {
            "root": {"depends_on": []},
            "left": {"depends_on": ["root"]},
            "right": {"depends_on": ["root"]},
            "bottom": {"depends_on": ["left", "right"]},
        }
        levels = compute_execution_plan_levels(["root"], graph)
        assert len(levels) == 3
        assert levels[0] == ["root"]
        assert sorted(levels[1]) == ["left", "right"]
        assert levels[2] == ["bottom"]

    def test_multiple_roots_same_level(self) -> None:
        """Test multiple independent roots in same level."""
        graph = {
            "a": {"depends_on": []},
            "b": {"depends_on": []},
            "c": {"depends_on": ["a", "b"]},
        }
        levels = compute_execution_plan_levels(["a", "b"], graph)
        assert len(levels) == 2
        assert sorted(levels[0]) == ["a", "b"]
        assert levels[1] == ["c"]


class TestOutputSlots:
    """Tests for _output_slots function."""

    def test_output_slots_exact(self) -> None:
        """Test outputting exact number of slots."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_slots(["a", "b", "c"], 3)
            output = mock_stdout.getvalue()
        assert "count=3" in output
        assert "key_01=a" in output
        assert "key_02=b" in output
        assert "key_03=c" in output

    def test_output_slots_more_slots_than_items(self) -> None:
        """Test outputting more slots than items."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_slots(["a", "b"], 4)
            output = mock_stdout.getvalue()
        assert "count=2" in output
        assert "key_01=a" in output
        assert "key_02=b" in output
        assert "key_03=" in output
        assert "key_04=" in output

    def test_output_slots_empty(self) -> None:
        """Test outputting with no items."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_slots([], 2)
            output = mock_stdout.getvalue()
        assert "count=0" in output
        assert "key_01=" in output
        assert "key_02=" in output


class TestOutputResults:
    """Tests for _output_results function."""

    def test_output_json(self) -> None:
        """Test JSON output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_results(["a", "b", "c"], "json")
            output = mock_stdout.getvalue().strip()
        assert output == '["a", "b", "c"]'

    def test_output_lines(self) -> None:
        """Test lines output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_results(["a", "b", "c"], "lines")
            output = mock_stdout.getvalue()
        assert output == "a\nb\nc\n"

    def test_output_indexed(self) -> None:
        """Test indexed JSON output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_results(["a", "b"], "json", indexed=True)
            output = mock_stdout.getvalue().strip()
        expected = '[{"idx": "01", "name": "a"}, {"idx": "02", "name": "b"}]'
        assert output == expected

    def test_output_empty(self) -> None:
        """Test output with empty list."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _output_results([], "json")
            output = mock_stdout.getvalue().strip()
        assert output == "[]"
