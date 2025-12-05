"""
Unit tests for lib/workflow_ordering.py.

Tests follow the testing pyramid principles from CLAUDE.md:
- Atomic tests: each test verifies one thing
- Single responsibility: one assertion per test
- Full coverage: every function, every branch
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from workflow_ordering import (
    CircularDependencyError,
    WorkflowConfig,
    WorkflowOrder,
    WorkflowOrderError,
    get_affected_workflows,
    get_all_dependencies,
    get_deployment_order,
    parse_workflow_order,
    should_wait_for,
)


@pytest.fixture
def valid_workflow_yaml() -> str:
    """Create a valid workflow order YAML file."""
    content = """
workflows:
  bootstrap:
    level: 0
    paths:
      - src/bootstrap/**
      - .github/workflows/bootstrap.yml
    depends_on: []

  ecr:
    level: 1
    paths:
      - .github/workflows/ecr.yml
    depends_on:
      - bootstrap

  www_shared:
    level: 1
    paths:
      - src/www/shared/**
      - .github/workflows/www_shared.yml
    depends_on:
      - bootstrap

  runners:
    level: 2
    paths:
      - src/api/endpoints/runners/**
      - .github/workflows/runners.yml
    depends_on:
      - ecr

  simulation_soc:
    level: 5
    paths:
      - src/api/endpoints/simulation_soc/**
      - .github/workflows/simulation_soc.yml
    depends_on:
      - runners
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        f.write(content)
        return f.name


@pytest.fixture
def circular_dependency_yaml() -> str:
    """Create a YAML file with circular dependencies."""
    content = """
workflows:
  a:
    level: 0
    paths: []
    depends_on:
      - b

  b:
    level: 0
    paths: []
    depends_on:
      - c

  c:
    level: 0
    paths: []
    depends_on:
      - a
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        f.write(content)
        return f.name


class TestParseWorkflowOrderValidInput:
    """Tests for parse_workflow_order with valid input."""

    def test_parses_workflow_names(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order extracts workflow names."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "bootstrap" in order.workflows

    def test_parses_all_workflows(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order extracts all workflows."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert len(order.workflows) == 5

    def test_parses_workflow_level(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order extracts workflow level."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert order.workflows["bootstrap"].level == 0

    def test_parses_workflow_paths(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order extracts workflow paths."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "src/bootstrap/**" in order.workflows["bootstrap"].paths

    def test_parses_workflow_depends_on(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order extracts depends_on."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "bootstrap" in order.workflows["ecr"].depends_on

    def test_groups_workflows_by_level(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order groups workflows by level."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "bootstrap" in order.levels[0]

    def test_level_1_has_two_workflows(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order groups level 1 workflows correctly."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert len(order.levels[1]) == 2

    def test_level_1_contains_ecr(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order includes ecr in level 1."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "ecr" in order.levels[1]

    def test_level_1_contains_www_shared(self, valid_workflow_yaml: str) -> None:
        """parse_workflow_order includes www_shared in level 1."""
        order = parse_workflow_order(valid_workflow_yaml)
        assert "www_shared" in order.levels[1]


class TestParseWorkflowOrderInvalidInput:
    """Tests for parse_workflow_order with invalid input."""

    def test_raises_on_missing_file(self) -> None:
        """parse_workflow_order raises on missing file."""
        with pytest.raises(WorkflowOrderError, match="not found"):
            parse_workflow_order("/nonexistent/file.yml")

    def test_raises_on_invalid_yaml(self) -> None:
        """parse_workflow_order raises on invalid YAML."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            with pytest.raises(WorkflowOrderError, match="Invalid YAML"):
                parse_workflow_order(f.name)

    def test_raises_on_non_mapping_root(self) -> None:
        """parse_workflow_order raises when root is not a mapping."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write("- item1\n- item2")
            f.flush()
            with pytest.raises(WorkflowOrderError, match="must contain a YAML mapping"):
                parse_workflow_order(f.name)

    def test_raises_on_missing_workflows_key(self) -> None:
        """parse_workflow_order raises when workflows key is missing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write("other_key: value")
            f.flush()
            with pytest.raises(WorkflowOrderError, match="must contain 'workflows'"):
                parse_workflow_order(f.name)

    def test_raises_on_missing_level(self) -> None:
        """parse_workflow_order raises when workflow has no level."""
        content = """
workflows:
  test:
    paths: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(content)
            f.flush()
            with pytest.raises(WorkflowOrderError, match="must have a 'level'"):
                parse_workflow_order(f.name)

    def test_raises_on_negative_level(self) -> None:
        """parse_workflow_order raises on negative level."""
        content = """
workflows:
  test:
    level: -1
    paths: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(content)
            f.flush()
            with pytest.raises(WorkflowOrderError, match="non-negative integer"):
                parse_workflow_order(f.name)

    def test_raises_on_unknown_dependency(self) -> None:
        """parse_workflow_order raises on unknown dependency."""
        content = """
workflows:
  test:
    level: 0
    paths: []
    depends_on:
      - nonexistent
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(content)
            f.flush()
            with pytest.raises(WorkflowOrderError, match="unknown workflow"):
                parse_workflow_order(f.name)

    def test_raises_on_circular_dependency(
        self, circular_dependency_yaml: str
    ) -> None:
        """parse_workflow_order raises on circular dependencies."""
        with pytest.raises(CircularDependencyError, match="Circular dependency"):
            parse_workflow_order(circular_dependency_yaml)


class TestGetAffectedWorkflows:
    """Tests for get_affected_workflows function."""

    def test_returns_empty_for_no_changes(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows returns empty set for no changes."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows([], order)
        assert len(affected) == 0

    def test_finds_affected_workflow_by_exact_path(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows finds workflow by exact path."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            [".github/workflows/bootstrap.yml"], order
        )
        assert "bootstrap" in affected

    def test_finds_affected_workflow_by_glob_pattern(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows finds workflow by glob pattern."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            ["src/bootstrap/main.tf"], order
        )
        assert "bootstrap" in affected

    def test_finds_affected_workflow_by_nested_path(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows finds workflow by deeply nested path."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            ["src/bootstrap/modules/oidc/main.tf"], order
        )
        assert "bootstrap" in affected

    def test_finds_multiple_affected_workflows(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows finds multiple affected workflows."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            [
                "src/bootstrap/main.tf",
                ".github/workflows/ecr.yml",
            ],
            order,
        )
        assert "bootstrap" in affected
        assert "ecr" in affected

    def test_returns_only_matching_workflows(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows returns only workflows with matching paths."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            ["src/unrelated/file.py"], order
        )
        assert len(affected) == 0

    def test_handles_leading_dot_slash(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_affected_workflows handles ./ prefix in paths."""
        order = parse_workflow_order(valid_workflow_yaml)
        affected = get_affected_workflows(
            ["./src/bootstrap/main.tf"], order
        )
        assert "bootstrap" in affected


class TestGetDeploymentOrder:
    """Tests for get_deployment_order function."""

    def test_returns_empty_for_no_affected(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order returns empty list for no affected workflows."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order(set(), order)
        assert result == []

    def test_returns_single_level_for_one_workflow(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order returns single level for one workflow."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"bootstrap"}, order)
        assert len(result) == 1

    def test_single_workflow_in_correct_level(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order puts single workflow in correct level."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"bootstrap"}, order)
        assert "bootstrap" in result[0]

    def test_returns_multiple_levels_for_dependent_workflows(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order returns multiple levels for dependent workflows."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"bootstrap", "ecr"}, order)
        assert len(result) == 2

    def test_bootstrap_before_ecr(self, valid_workflow_yaml: str) -> None:
        """get_deployment_order puts bootstrap before ecr."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"bootstrap", "ecr"}, order)
        assert result[0] == ["bootstrap"]
        assert result[1] == ["ecr"]

    def test_groups_same_level_workflows(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order groups workflows at same level."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"ecr", "www_shared"}, order)
        assert len(result) == 1
        assert len(result[0]) == 2

    def test_sorts_workflows_within_level(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order sorts workflows alphabetically within level."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order({"ecr", "www_shared"}, order)
        assert result[0] == ["ecr", "www_shared"]

    def test_handles_diamond_dependency(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_deployment_order handles diamond dependency pattern."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = get_deployment_order(
            {"bootstrap", "ecr", "www_shared", "runners"}, order
        )
        assert len(result) == 3
        assert result[0] == ["bootstrap"]
        assert "ecr" in result[1]
        assert "www_shared" in result[1]
        assert result[2] == ["runners"]


class TestShouldWaitFor:
    """Tests for should_wait_for function."""

    def test_returns_none_when_no_deps(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for returns None when workflow has no dependencies."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = should_wait_for("bootstrap", set(), order)
        assert result is None

    def test_returns_none_when_all_deps_complete(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for returns None when all dependencies are complete."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = should_wait_for("ecr", {"bootstrap"}, order)
        assert result is None

    def test_returns_missing_explicit_dep(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for returns missing explicit dependency."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = should_wait_for("ecr", set(), order)
        assert result == "bootstrap"

    def test_returns_missing_level_dep(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for returns missing level-based dependency."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = should_wait_for("runners", {"ecr"}, order)
        assert result == "bootstrap"

    def test_returns_none_for_unknown_workflow(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for returns None for unknown workflow."""
        order = parse_workflow_order(valid_workflow_yaml)
        result = should_wait_for("nonexistent", set(), order)
        assert result is None

    def test_checks_all_lower_levels(
        self, valid_workflow_yaml: str
    ) -> None:
        """should_wait_for checks all lower level workflows."""
        order = parse_workflow_order(valid_workflow_yaml)
        # runners is level 2, needs level 0 and level 1 complete
        result = should_wait_for(
            "runners", {"bootstrap", "ecr"}, order
        )
        # www_shared is also level 1 and not complete
        assert result == "www_shared"


class TestGetAllDependencies:
    """Tests for get_all_dependencies function."""

    def test_returns_empty_for_no_deps(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_all_dependencies returns empty set for workflow with no deps."""
        order = parse_workflow_order(valid_workflow_yaml)
        deps = get_all_dependencies("bootstrap", order)
        assert len(deps) == 0

    def test_returns_direct_dependencies(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_all_dependencies returns direct dependencies."""
        order = parse_workflow_order(valid_workflow_yaml)
        deps = get_all_dependencies("ecr", order)
        assert "bootstrap" in deps

    def test_returns_transitive_dependencies(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_all_dependencies returns transitive dependencies."""
        order = parse_workflow_order(valid_workflow_yaml)
        deps = get_all_dependencies("runners", order)
        assert "bootstrap" in deps
        assert "ecr" in deps

    def test_includes_all_lower_level_workflows(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_all_dependencies includes all workflows from lower levels."""
        order = parse_workflow_order(valid_workflow_yaml)
        deps = get_all_dependencies("runners", order)
        assert "www_shared" in deps

    def test_returns_empty_for_unknown_workflow(
        self, valid_workflow_yaml: str
    ) -> None:
        """get_all_dependencies returns empty set for unknown workflow."""
        order = parse_workflow_order(valid_workflow_yaml)
        deps = get_all_dependencies("nonexistent", order)
        assert len(deps) == 0


class TestWorkflowConfigDataclass:
    """Tests for WorkflowConfig dataclass."""

    def test_creates_with_all_fields(self) -> None:
        """WorkflowConfig creates instance with all fields."""
        config = WorkflowConfig(
            name="test",
            level=1,
            paths=["src/**"],
            depends_on=["other"],
        )
        assert config.name == "test"
        assert config.level == 1
        assert config.paths == ["src/**"]
        assert config.depends_on == ["other"]

    def test_defaults_paths_to_empty_list(self) -> None:
        """WorkflowConfig defaults paths to empty list."""
        config = WorkflowConfig(name="test", level=0)
        assert config.paths == []

    def test_defaults_depends_on_to_empty_list(self) -> None:
        """WorkflowConfig defaults depends_on to empty list."""
        config = WorkflowConfig(name="test", level=0)
        assert config.depends_on == []


class TestWorkflowOrderDataclass:
    """Tests for WorkflowOrder dataclass."""

    def test_creates_with_defaults(self) -> None:
        """WorkflowOrder creates instance with default empty dicts."""
        order = WorkflowOrder()
        assert order.workflows == {}

    def test_levels_is_defaultdict(self) -> None:
        """WorkflowOrder levels is a defaultdict."""
        order = WorkflowOrder()
        # Accessing non-existent key should return empty list
        assert order.levels[99] == []
