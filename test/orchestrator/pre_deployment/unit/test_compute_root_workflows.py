"""Unit tests for compute_root_workflows.py."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from compute_root_workflows import (  # pylint: disable=wrong-import-position
    compute_root_workflows,
    file_matches_patterns,
    get_affected_workflows,
    get_all_ancestors,
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
            ".github/workflows/image_for_ecs_runners.yml",
            "src/api/endpoints/image_for_ecs_runners/**",
        ],
    },
    "ecs_runner": {
        "name": "ECS Runner",
        "depends_on": ["image_for_ecs_runners"],
        "paths": [
            ".github/workflows/ecs_runner.yml",
            "src/api/endpoints/ecs_runner/**",
        ],
    },
    "contact": {
        "name": "Contact",
        "depends_on": ["ecs_runner"],
        "paths": [".github/workflows/contact.yml", "src/api/endpoints/contact/**"],
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
