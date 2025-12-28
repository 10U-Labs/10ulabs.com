"""Unit tests for compute_roots.py."""

import io
from unittest.mock import patch

import pytest

from conftest import EXTENDED_LINEAR_GRAPH


class TestFileMatchesPatterns:
    """Tests for file_matches_patterns function."""

    @pytest.mark.parametrize(
        "file_path,patterns,expected",
        [
            # Exact match cases
            (".github/workflows/bootstrap.yml", [".github/workflows/bootstrap.yml"], True),
            (".github/workflows/api_shared_routing.yml", [".github/workflows/bootstrap.yml"], False),
            # Single glob * cases (matches any characters including /)
            ("src/main.tf", ["src/*.tf"], True),
            ("src/sub/main.tf", ["src/*.tf"], True),
            # Double star ** cases
            ("src/bootstrap/main.tf", ["src/bootstrap/**"], True),
            ("src/bootstrap/sub/file.tf", ["src/bootstrap/**"], True),
            ("src/api/main.tf", ["src/bootstrap/**"], False),
            # Multiple pattern cases
            (".github/workflows/bootstrap.yml", [".github/workflows/bootstrap.yml", "src/bootstrap/**"], True),
            ("src/bootstrap/main.tf", [".github/workflows/bootstrap.yml", "src/bootstrap/**"], True),
            ("src/api/main.tf", [".github/workflows/bootstrap.yml", "src/bootstrap/**"], False),
            # Empty patterns
            ("any/file.txt", [], False),
        ],
        ids=[
            "exact_match_true",
            "exact_match_false",
            "glob_star_direct_child",
            "glob_star_nested_child",
            "double_star_direct_child",
            "double_star_nested_child",
            "double_star_different_path",
            "multiple_patterns_first",
            "multiple_patterns_second",
            "multiple_patterns_no_match",
            "empty_patterns",
        ],
    )
    def test_file_matches_patterns(
        self, compute_roots, file_path: str, patterns: list, expected: bool
    ) -> None:
        """Test file_matches_patterns with various inputs."""
        result = compute_roots.file_matches_patterns(file_path, patterns)
        assert result == expected


class TestGetAllAncestors:
    """Tests for get_all_ancestors function."""

    def test_no_ancestors(self, compute_roots) -> None:
        """Test workflow with no dependencies."""
        ancestors = compute_roots.get_all_ancestors("bootstrap", EXTENDED_LINEAR_GRAPH)
        assert ancestors == set()

    def test_single_ancestor(self, compute_roots) -> None:
        """Test workflow with one direct dependency."""
        ancestors = compute_roots.get_all_ancestors("www_shared", EXTENDED_LINEAR_GRAPH)
        assert ancestors == {"bootstrap"}

    def test_transitive_ancestors(self, compute_roots) -> None:
        """Test workflow with transitive dependencies."""
        ancestors = compute_roots.get_all_ancestors("api", EXTENDED_LINEAR_GRAPH)
        assert ancestors == {"bootstrap", "www_shared"}

    def test_deep_ancestors(self, compute_roots) -> None:
        """Test workflow deep in the dependency chain."""
        ancestors = compute_roots.get_all_ancestors("contact", EXTENDED_LINEAR_GRAPH)
        expected = {
            "bootstrap",
            "www_shared",
            "api",
            "health",
            "ecr",
            "ecs_images",
            "ecs_runner",
        }
        assert ancestors == expected

    def test_caching_stores_target_workflow(self, compute_roots) -> None:
        """Test that ancestor computation caches target workflow."""
        cache: dict[str, set[str]] = {}
        compute_roots.get_all_ancestors("api", EXTENDED_LINEAR_GRAPH, cache)
        assert "api" in cache

    def test_caching_stores_direct_ancestor(self, compute_roots) -> None:
        """Test that ancestor computation caches direct ancestor."""
        cache: dict[str, set[str]] = {}
        compute_roots.get_all_ancestors("api", EXTENDED_LINEAR_GRAPH, cache)
        assert "www_shared" in cache

    def test_caching_stores_transitive_ancestor(self, compute_roots) -> None:
        """Test that ancestor computation caches transitive ancestor."""
        cache: dict[str, set[str]] = {}
        compute_roots.get_all_ancestors("api", EXTENDED_LINEAR_GRAPH, cache)
        assert "bootstrap" in cache


class TestGetAffectedWorkflows:
    """Tests for get_affected_workflows function."""

    def test_single_file_single_workflow(self, compute_roots) -> None:
        """Test single file affecting single workflow."""
        changed = ["src/bootstrap/main.tf"]
        affected = compute_roots.get_affected_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert affected == {"bootstrap"}

    def test_single_file_workflow_file(self, compute_roots) -> None:
        """Test changing a workflow file itself."""
        changed = [".github/workflows/api_shared_routing.yml"]
        affected = compute_roots.get_affected_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert affected == {"api"}

    def test_multiple_files_single_workflow(self, compute_roots) -> None:
        """Test multiple files affecting single workflow."""
        changed = ["src/bootstrap/main.tf", "src/bootstrap/variables.tf"]
        affected = compute_roots.get_affected_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert affected == {"bootstrap"}

    def test_multiple_files_multiple_workflows(self, compute_roots) -> None:
        """Test files affecting multiple workflows."""
        changed = ["src/bootstrap/main.tf", "src/api/shared/routing/main.tf"]
        affected = compute_roots.get_affected_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert affected == {"bootstrap", "api"}

    def test_no_matching_files(self, compute_roots) -> None:
        """Test with files that don't match any workflow."""
        changed = ["README.md", "docs/guide.md"]
        affected = compute_roots.get_affected_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert affected == set()


class TestComputeRootWorkflows:
    """Tests for compute_root_workflows function."""

    def test_single_root_workflow(self, compute_roots) -> None:
        """Test single workflow change returns that workflow as root."""
        changed = ["src/bootstrap/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert roots == ["bootstrap"]

    def test_ancestor_and_descendant_changed(self, compute_roots) -> None:
        """Test that only ancestor is returned when both are changed."""
        changed = ["src/bootstrap/main.tf", "src/www/shared/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
        # Only bootstrap should be root; www_shared will cascade
        assert roots == ["bootstrap"]

    def test_deep_chain_only_root(self, compute_roots) -> None:
        """Test deep chain returns only the root."""
        changed = [
            "src/bootstrap/main.tf",
            "src/www/shared/main.tf",
            "src/api/shared/routing/main.tf",
            "src/api/operational/health/main.tf",
        ]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert roots == ["bootstrap"]

    def test_independent_workflows(self, compute_roots) -> None:
        """Test multiple independent workflow changes."""
        # Create a graph with two independent branches
        graph = {
            "a": {"depends_on": [], "paths": ["src/a/**"]},
            "b": {"depends_on": [], "paths": ["src/b/**"]},
            "c": {"depends_on": ["a"], "paths": ["src/c/**"]},
            "d": {"depends_on": ["b"], "paths": ["src/d/**"]},
        }
        changed = ["src/a/file.tf", "src/b/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, graph)
        assert sorted(roots) == ["a", "b"]

    def test_middle_of_chain(self, compute_roots) -> None:
        """Test changing middle of chain returns that workflow as root."""
        changed = ["src/api/shared/routing/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert roots == ["api"]

    def test_no_changes(self, compute_roots) -> None:
        """Test empty file list returns empty roots."""
        roots = compute_roots.compute_root_workflows([], EXTENDED_LINEAR_GRAPH)
        assert roots == []

    def test_unrelated_files(self, compute_roots) -> None:
        """Test files not matching any workflow return empty roots."""
        changed = ["README.md"]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
        assert roots == []

    def test_leaf_workflow_only(self, compute_roots) -> None:
        """Test changing only a leaf workflow returns it as root."""
        changed = ["src/api/endpoints/contact/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, EXTENDED_LINEAR_GRAPH)
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

    def test_diamond_root_change(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing root in diamond returns only root."""
        changed = ["src/root/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]

    def test_diamond_both_middle(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing both middle nodes returns both as roots."""
        changed = ["src/left/file.tf", "src/right/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert sorted(roots) == ["left", "right"]

    def test_diamond_one_middle_and_bottom(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing one middle and bottom returns only middle."""
        changed = ["src/left/file.tf", "src/bottom/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        # Only left is root; bottom has left as ancestor
        assert roots == ["left"]

    def test_diamond_all_nodes(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing all nodes returns only root."""
        changed = [
            "src/root/file.tf",
            "src/left/file.tf",
            "src/right/file.tf",
            "src/bottom/file.tf",
        ]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_no_descendants(self, utils) -> None:
        """Test leaf workflow with no dependents."""
        descendants = utils.get_all_descendants("contact", EXTENDED_LINEAR_GRAPH)
        assert descendants == set()

    def test_single_descendant(self, utils) -> None:
        """Test workflow with one direct dependent."""
        descendants = utils.get_all_descendants("ecs_runner", EXTENDED_LINEAR_GRAPH)
        assert descendants == {"contact"}

    def test_transitive_descendants(self, utils) -> None:
        """Test workflow with transitive dependents."""
        descendants = utils.get_all_descendants("ecr", EXTENDED_LINEAR_GRAPH)
        assert descendants == {"ecs_images", "ecs_runner", "contact"}

    def test_root_descendants(self, utils) -> None:
        """Test root workflow has all others as descendants."""
        descendants = utils.get_all_descendants("bootstrap", EXTENDED_LINEAR_GRAPH)
        expected = {
            "www_shared",
            "api",
            "health",
            "ecr",
            "ecs_images",
            "ecs_runner",
            "contact",
        }
        assert descendants == expected

    def test_caching_stores_target_workflow(self, utils) -> None:
        """Test that descendant computation caches target workflow."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("ecr", EXTENDED_LINEAR_GRAPH, cache)
        assert "ecr" in cache

    def test_caching_stores_direct_descendant(self, utils) -> None:
        """Test that descendant computation caches direct descendant."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("ecr", EXTENDED_LINEAR_GRAPH, cache)
        assert "ecs_images" in cache

    def test_caching_stores_second_level_descendant(self, utils) -> None:
        """Test that descendant computation caches second level descendant."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("ecr", EXTENDED_LINEAR_GRAPH, cache)
        assert "ecs_runner" in cache

    def test_caching_stores_leaf_descendant(self, utils) -> None:
        """Test that descendant computation caches leaf descendant."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("ecr", EXTENDED_LINEAR_GRAPH, cache)
        assert "contact" in cache


class TestInsertSorted:
    """Tests for insert_sorted function."""

    def test_insert_into_empty_list(self, compute_roots) -> None:
        """Test inserting into empty list."""
        queue: list[str] = []
        compute_roots.insert_sorted(queue, "b")
        assert queue == ["b"]

    def test_insert_at_beginning(self, compute_roots) -> None:
        """Test inserting at beginning of list."""
        queue = ["c", "d", "e"]
        compute_roots.insert_sorted(queue, "a")
        assert queue == ["a", "c", "d", "e"]

    def test_insert_at_end(self, compute_roots) -> None:
        """Test inserting at end of list."""
        queue = ["a", "b", "c"]
        compute_roots.insert_sorted(queue, "z")
        assert queue == ["a", "b", "c", "z"]

    def test_insert_in_middle(self, compute_roots) -> None:
        """Test inserting in middle of list."""
        queue = ["a", "c", "e"]
        compute_roots.insert_sorted(queue, "b")
        assert queue == ["a", "b", "c", "e"]

    def test_insert_duplicate(self, compute_roots) -> None:
        """Test inserting duplicate value."""
        queue = ["a", "c", "e"]
        compute_roots.insert_sorted(queue, "c")
        assert queue == ["a", "c", "c", "e"]


class TestTopologicalSort:
    """Tests for topological_sort function."""

    def test_single_workflow(self, compute_roots) -> None:
        """Test sorting single workflow."""
        workflows = {"bootstrap"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        assert result == ["bootstrap"]

    def test_linear_chain(self, compute_roots) -> None:
        """Test sorting linear dependency chain."""
        workflows = {"bootstrap", "www_shared", "api"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        assert result == ["bootstrap", "www_shared", "api"]

    def test_respects_dependencies_bootstrap_before_www_shared(self, compute_roots) -> None:
        """Test that bootstrap comes before www_shared."""
        workflows = {"api", "bootstrap", "www_shared", "health"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        assert result.index("bootstrap") < result.index("www_shared")

    def test_respects_dependencies_www_shared_before_api(self, compute_roots) -> None:
        """Test that www_shared comes before api."""
        workflows = {"api", "bootstrap", "www_shared", "health"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        assert result.index("www_shared") < result.index("api")

    def test_respects_dependencies_api_before_health(self, compute_roots) -> None:
        """Test that api comes before health."""
        workflows = {"api", "bootstrap", "www_shared", "health"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        assert result.index("api") < result.index("health")

    def test_diamond_pattern_ordering(self, compute_roots) -> None:
        """Test diamond-shaped graph maintains correct ordering."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        result = compute_roots.topological_sort({"root", "left", "right", "bottom"}, graph)
        assert (result[0], result[-1],
                result.index("left") < result.index("bottom"),
                result.index("right") < result.index("bottom")) == (
                    "root", "bottom", True, True)

    def test_partial_graph(self, compute_roots) -> None:
        """Test sorting subset of graph."""
        workflows = {"api", "health"}
        result = compute_roots.topological_sort(workflows, EXTENDED_LINEAR_GRAPH)
        # api must come before health
        assert result == ["api", "health"]


class TestTopologicalSortLevels:
    """Tests for topological_sort_levels function."""

    def test_single_workflow(self, compute_roots) -> None:
        """Test single workflow returns single level."""
        levels = compute_roots.topological_sort_levels({"bootstrap"}, EXTENDED_LINEAR_GRAPH)
        assert levels == [["bootstrap"]]

    def test_linear_chain(self, compute_roots) -> None:
        """Test linear chain returns one workflow per level."""
        levels = compute_roots.topological_sort_levels({"bootstrap", "www_shared", "api"},
                                         EXTENDED_LINEAR_GRAPH)
        assert levels == [["bootstrap"], ["www_shared"], ["api"]]

    def test_parallel_workflows_structure(self, compute_roots) -> None:
        """Test parallel workflows are grouped correctly by level."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        levels = compute_roots.topological_sort_levels({"root", "left", "right", "bottom"},
                                         graph)
        assert (len(levels), levels[0], sorted(levels[1]), levels[2]) == (
            3, ["root"], ["left", "right"], ["bottom"])

    def test_complex_parallel_structure(self, compute_roots) -> None:
        """Test complex parallel graph levels are correct."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": ["a"]},
                 "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]},
                 "e": {"depends_on": ["c"]}, "f": {"depends_on": ["d", "e"]}}
        levels = compute_roots.topological_sort_levels({"a", "b", "c", "d", "e", "f"}, graph)
        assert (len(levels), levels[0], sorted(levels[1]), sorted(levels[2]),
                levels[3]) == (4, ["a"], ["b", "c"], ["d", "e"], ["f"])


class TestComputeExecutionPlan:
    """Tests for compute_execution_plan function."""

    def test_single_root_no_descendants(self, compute_roots) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        plan = compute_roots.compute_execution_plan(["a"], graph)
        assert plan == ["a"]

    def test_single_root_with_descendants(self, compute_roots) -> None:
        """Test single root includes all descendants."""
        plan = compute_roots.compute_execution_plan(["bootstrap"], EXTENDED_LINEAR_GRAPH)
        expected = [
            "bootstrap",
            "www_shared",
            "api",
            "health",
            "ecr",
            "ecs_images",
            "ecs_runner",
            "contact",
        ]
        assert plan == expected

    def test_middle_root(self, compute_roots) -> None:
        """Test starting from middle of chain."""
        plan = compute_roots.compute_execution_plan(["ecr"], EXTENDED_LINEAR_GRAPH)
        expected = ["ecr", "ecs_images", "ecs_runner", "contact"]
        assert plan == expected

    def test_multiple_roots_execution_order(self, compute_roots) -> None:
        """Test multiple roots include all descendants in correct order."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                 "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]}}
        plan = compute_roots.compute_execution_plan(["a", "b"], graph)
        assert (set(plan), plan.index("a") < plan.index("c"),
                plan.index("b") < plan.index("d")) == (
                    {"a", "b", "c", "d"}, True, True)


class TestComputeExecutionPlanLevels:
    """Tests for compute_execution_plan_levels function."""

    def test_single_root_no_descendants(self, compute_roots) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        levels = compute_roots.compute_execution_plan_levels(["a"], graph)
        assert levels == [["a"]]

    def test_single_root_with_descendants_has_eight_levels(self, compute_roots) -> None:
        """Test single root with descendants has 8 levels."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], EXTENDED_LINEAR_GRAPH)
        assert len(levels) == 8

    def test_single_root_with_descendants_bootstrap_first(self, compute_roots) -> None:
        """Test single root with descendants has bootstrap first."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], EXTENDED_LINEAR_GRAPH)
        assert levels[0] == ["bootstrap"]

    def test_single_root_with_descendants_contact_last(self, compute_roots) -> None:
        """Test single root with descendants has contact last."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], EXTENDED_LINEAR_GRAPH)
        assert levels[-1] == ["contact"]

    def test_parallel_branches_level_structure(self, compute_roots) -> None:
        """Test parallel branches graph has correct level structure."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        levels = compute_roots.compute_execution_plan_levels(["root"], graph)
        assert (len(levels), levels[0], sorted(levels[1]), levels[2]) == (
            3, ["root"], ["left", "right"], ["bottom"])

    def test_multiple_roots_same_level_structure(self, compute_roots) -> None:
        """Test multiple independent roots level structure."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                 "c": {"depends_on": ["a", "b"]}}
        levels = compute_roots.compute_execution_plan_levels(["a", "b"], graph)
        assert (len(levels), sorted(levels[0]), levels[1]) == (
            2, ["a", "b"], ["c"])


class TestOutputSlots:
    """Tests for output_slots function."""

    @pytest.mark.parametrize(
        "items,num_slots,expected_in_output",
        [
            # Exact slots (3 items, 3 slots)
            (["a", "b", "c"], 3, "count=3"),
            (["a", "b", "c"], 3, "key_01=a"),
            (["a", "b", "c"], 3, "key_02=b"),
            (["a", "b", "c"], 3, "key_03=c"),
            # More slots than items (2 items, 4 slots)
            (["a", "b"], 4, "count=2"),
            (["a", "b"], 4, "key_01=a"),
            (["a", "b"], 4, "key_02=b"),
            (["a", "b"], 4, "key_03="),
            (["a", "b"], 4, "key_04="),
            # Empty list (0 items, 2 slots)
            ([], 2, "count=0"),
            ([], 2, "key_01="),
            ([], 2, "key_02="),
        ],
        ids=[
            "exact_slots_count",
            "exact_slots_key_01",
            "exact_slots_key_02",
            "exact_slots_key_03",
            "more_slots_count",
            "more_slots_key_01",
            "more_slots_key_02",
            "more_slots_empty_key_03",
            "more_slots_empty_key_04",
            "empty_list_count",
            "empty_list_empty_key_01",
            "empty_list_empty_key_02",
        ],
    )
    def test_output_slots(
        self, compute_roots, items: list, num_slots: int, expected_in_output: str
    ) -> None:
        """Test output_slots with various inputs."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(items, num_slots)
            output = mock_stdout.getvalue()
        assert expected_in_output in output


class TestOutputResults:
    """Tests for output_results function."""

    def test_output_json_object(self, compute_roots) -> None:
        """Test JSON object output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results(["a", "b", "c"])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": ["a", "b", "c"]}'

    def test_output_indexed(self, compute_roots) -> None:
        """Test indexed JSON output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results(["a", "b"], indexed=True)
            output = mock_stdout.getvalue().strip()
        expected = '{"workflows": [{"idx": "01", "name": "a"}, {"idx": "02", "name": "b"}]}'
        assert output == expected

    def test_output_empty(self, compute_roots) -> None:
        """Test output with empty list."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results([])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": []}'


class TestOutputLevelsIndexed:
    """Tests for output_levels_indexed function."""

    def test_single_level(self, compute_roots) -> None:
        """Test output with single level."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([["a", "b"]])
            output = mock_stdout.getvalue().strip()
        expected = (
            '{"workflows": [{"idx": "01", "level": 1, "name": "a"}, '
            '{"idx": "02", "level": 1, "name": "b"}]}'
        )
        assert output == expected

    def test_multiple_levels(self, compute_roots) -> None:
        """Test output with multiple levels."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([["a"], ["b", "c"], ["d"]])
            output = mock_stdout.getvalue().strip()
        expected = (
            '{"workflows": [{"idx": "01", "level": 1, "name": "a"}, '
            '{"idx": "02", "level": 2, "name": "b"}, '
            '{"idx": "03", "level": 2, "name": "c"}, '
            '{"idx": "04", "level": 3, "name": "d"}]}'
        )
        assert output == expected

    def test_empty_levels(self, compute_roots) -> None:
        """Test output with empty levels list."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": []}'


class TestComputeMergeRoots:
    """Tests for compute_merge_roots function.

    This function merges running workflows with new root workflows to find
    the optimal restart point when a new workflowctl run starts while
    workflows from a previous run are still executing.
    """

    def test_no_running_workflows(self, compute_roots) -> None:
        """Test with no running workflows returns new roots unchanged."""
        new_roots = ["api"]
        running: list[str] = []
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        assert result == ["api"]

    def test_no_new_roots(self, compute_roots) -> None:
        """Test with no new roots returns empty (let running workflows finish)."""
        new_roots: list[str] = []
        running = ["api"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        assert result == []

    def test_both_empty(self, compute_roots) -> None:
        """Test with both empty returns empty."""
        result = compute_roots.compute_merge_roots([], [], EXTENDED_LINEAR_GRAPH)
        assert result == []

    def test_running_downstream_of_new_root(self, compute_roots) -> None:
        """Test when running workflow is downstream of new changes.

        Scenario: Chain at api, new changes affect www_shared
        www_shared is upstream of api, so merge root is www_shared.
        """
        running = ["api"]
        new_roots = ["www_shared"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        # www_shared is ancestor of api, so www_shared is the merge root
        assert result == ["www_shared"]

    def test_running_upstream_of_new_root(self, compute_roots) -> None:
        """Test when running workflow is upstream of new changes.

        Scenario: Chain at www_shared, new changes affect health
        www_shared is upstream of health, so merge root is www_shared.
        """
        running = ["www_shared"]
        new_roots = ["health"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        # www_shared is ancestor of health, so www_shared is the merge root
        assert result == ["www_shared"]

    def test_running_and_new_same_level(self, compute_roots) -> None:
        """Test when running and new are at the same workflow.

        Scenario: Chain at api, new changes also affect api
        Merge root should be api.
        """
        running = ["api"]
        new_roots = ["api"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        assert result == ["api"]

    def test_unrelated_branches(self, compute_roots) -> None:
        """Test when running and new are in unrelated branches.

        Using diamond graph where left and right are independent.
        """
        graph = {
            "root": {"depends_on": [], "name": "Root"},
            "left": {"depends_on": ["root"], "name": "Left"},
            "right": {"depends_on": ["root"], "name": "Right"},
            "bottom": {"depends_on": ["left", "right"], "name": "Bottom"},
        }
        running = ["left"]
        new_roots = ["right"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # Both are independent branches, both should be roots
        assert sorted(result) == ["left", "right"]

    def test_running_at_common_ancestor(self, compute_roots) -> None:
        """Test when running workflow is ancestor of new changes.

        Scenario: Running at bootstrap, new changes affect api
        bootstrap is ancestor of api, so bootstrap is the merge root.
        """
        running = ["bootstrap"]
        new_roots = ["api"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        assert result == ["bootstrap"]

    def test_multiple_running_workflows(self, compute_roots) -> None:
        """Test with multiple running workflows from parallel branches."""
        graph = {
            "root": {"depends_on": [], "name": "Root"},
            "left": {"depends_on": ["root"], "name": "Left"},
            "right": {"depends_on": ["root"], "name": "Right"},
            "left_child": {"depends_on": ["left"], "name": "Left Child"},
            "right_child": {"depends_on": ["right"], "name": "Right Child"},
        }
        running = ["left_child", "right_child"]
        new_roots = ["root"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # root is ancestor of both, so root is the only merge root
        assert result == ["root"]

    def test_multiple_new_roots(self, compute_roots) -> None:
        """Test with multiple new root workflows."""
        graph = {
            "a": {"depends_on": [], "name": "A"},
            "b": {"depends_on": [], "name": "B"},
            "c": {"depends_on": ["a"], "name": "C"},
            "d": {"depends_on": ["b"], "name": "D"},
        }
        running = ["c"]
        new_roots = ["a", "b"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # a is ancestor of c, so only a and b are roots
        assert sorted(result) == ["a", "b"]

    def test_deep_chain_merge(self, compute_roots) -> None:
        """Test merge in deep dependency chain.

        Scenario: Running at health, new changes affect www_shared
        Should restart from www_shared.
        """
        running = ["health"]
        new_roots = ["www_shared"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        assert result == ["www_shared"]

    def test_unknown_running_workflow_filtered(self, compute_roots) -> None:
        """Test that unknown workflow keys are filtered out."""
        running = ["unknown_workflow"]
        new_roots = ["api"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        # Unknown workflow is filtered, only api remains
        assert result == ["api"]

    def test_mix_of_known_and_unknown(self, compute_roots) -> None:
        """Test with mix of known and unknown workflows."""
        running = ["api", "unknown_workflow"]
        new_roots = ["www_shared"]
        result = compute_roots.compute_merge_roots(running, new_roots, EXTENDED_LINEAR_GRAPH)
        # www_shared is ancestor of api, unknown is filtered
        assert result == ["www_shared"]
