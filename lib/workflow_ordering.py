"""
Workflow ordering module for managing deployment dependencies.

This module provides functions to parse, analyze, and order GitHub Actions
workflows based on their dependencies. Workflows are ordered in levels:

    Level 0: bootstrap.yml (foundation - IAM, S3, Route53)
    Level 1: ecr.yml, www_shared.yml (shared resources)
    Level 2: runners.yml, api.yml (runner infra, API Gateway)
    Level 3: image_for_ecs_runners.yml, image_for_ec2_runners_*.yml (runner images)
    Level 4: ecs_runner.yml, ec2_runner.yml (runner endpoints)
    Level 5: All other endpoints

When a commit affects multiple levels, workflows deploy in order.
When a commit affects only one workflow, it deploys independently.
"""

import fnmatch
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import yaml


@dataclass
class WorkflowConfig:
    """Configuration for a single workflow."""

    name: str
    level: int
    paths: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


@dataclass
class WorkflowOrder:
    """Parsed workflow ordering configuration."""

    workflows: Dict[str, WorkflowConfig] = field(default_factory=dict)
    levels: Dict[int, List[str]] = field(default_factory=lambda: defaultdict(list))


class WorkflowOrderError(Exception):
    """Raised when workflow ordering operations fail."""


class CircularDependencyError(WorkflowOrderError):
    """Raised when circular dependencies are detected."""


def _load_yaml_file(yaml_path: Union[str, Path]) -> dict:
    """Load and validate a YAML file exists and contains a mapping."""
    path = Path(yaml_path)

    if not path.exists():
        raise WorkflowOrderError(f"Workflow order file not found: {yaml_path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise WorkflowOrderError(f"Invalid YAML in {yaml_path}: {e}") from e

    if not isinstance(data, dict):
        raise WorkflowOrderError(
            f"Workflow order file must contain a YAML mapping, got: {type(data).__name__}"
        )

    return data


def _parse_workflow_config(name: str, config: dict) -> WorkflowConfig:
    """Parse and validate a single workflow configuration."""
    if not isinstance(config, dict):
        raise WorkflowOrderError(f"Workflow '{name}' configuration must be a mapping")

    level = config.get("level")
    if level is None:
        raise WorkflowOrderError(f"Workflow '{name}' must have a 'level'")
    if not isinstance(level, int) or level < 0:
        raise WorkflowOrderError(
            f"Workflow '{name}' level must be a non-negative integer"
        )

    paths = config.get("paths", [])
    if not isinstance(paths, list):
        raise WorkflowOrderError(f"Workflow '{name}' paths must be a list")

    depends_on = config.get("depends_on", [])
    if not isinstance(depends_on, list):
        raise WorkflowOrderError(f"Workflow '{name}' depends_on must be a list")

    return WorkflowConfig(name=name, level=level, paths=paths, depends_on=depends_on)


def _validate_dependencies(order: WorkflowOrder) -> None:
    """Validate that all workflow dependencies reference existing workflows."""
    for name, workflow in order.workflows.items():
        for dep in workflow.depends_on:
            if dep not in order.workflows:
                raise WorkflowOrderError(
                    f"Workflow '{name}' depends on unknown workflow '{dep}'"
                )


def parse_workflow_order(yaml_path: Union[str, Path]) -> WorkflowOrder:
    """
    Parse a workflow order YAML file into a WorkflowOrder object.

    Args:
        yaml_path: Path to the workflow-order.yml file.

    Returns:
        WorkflowOrder with workflows and levels populated.

    Raises:
        WorkflowOrderError: If the YAML is invalid or malformed.
        CircularDependencyError: If circular dependencies are detected.
    """
    data = _load_yaml_file(yaml_path)

    if "workflows" not in data:
        raise WorkflowOrderError("Workflow order file must contain 'workflows' key")

    workflows_data = data["workflows"]
    if not isinstance(workflows_data, dict):
        raise WorkflowOrderError("'workflows' must be a mapping")

    order = WorkflowOrder()

    for name, config in workflows_data.items():
        workflow = _parse_workflow_config(name, config)
        order.workflows[name] = workflow
        order.levels[workflow.level].append(name)

    _validate_dependencies(order)
    _check_circular_dependencies(order)

    return order


def _check_circular_dependencies(order: WorkflowOrder) -> None:
    """
    Check for circular dependencies in the workflow graph.

    Args:
        order: WorkflowOrder to check.

    Raises:
        CircularDependencyError: If circular dependencies are detected.
    """
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def visit(name: str, path: List[str]) -> None:
        if name in rec_stack:
            cycle = path[path.index(name) :] + [name]
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        if name in visited:
            return

        visited.add(name)
        rec_stack.add(name)

        workflow = order.workflows[name]
        for dep in workflow.depends_on:
            visit(dep, path + [name])

        rec_stack.remove(name)

    for name in order.workflows:
        visit(name, [])


def get_affected_workflows(
    changed_files: List[str], order: WorkflowOrder
) -> Set[str]:
    """
    Determine which workflows are affected by a set of changed files.

    Args:
        changed_files: List of changed file paths.
        order: WorkflowOrder configuration.

    Returns:
        Set of affected workflow names.
    """
    affected: Set[str] = set()

    for file_path in changed_files:
        for name, workflow in order.workflows.items():
            for pattern in workflow.paths:
                if _matches_pattern(file_path, pattern):
                    affected.add(name)
                    break

    return affected


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """
    Check if a file path matches a glob pattern.

    Args:
        file_path: File path to check.
        pattern: Glob pattern (supports * and ** wildcards).

    Returns:
        True if the path matches the pattern.
    """
    # Handle negation patterns (e.g., "!src/docs/**")
    if pattern.startswith("!"):
        return False  # Negation patterns don't add to affected

    # Normalize paths
    file_path = file_path.lstrip("./")
    pattern = pattern.lstrip("./")

    # Use fnmatch for glob matching
    if "**" in pattern:
        # For ** patterns, we need recursive matching
        pattern_parts = pattern.split("**")
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            prefix = prefix.rstrip("/")
            suffix = suffix.lstrip("/")

            if prefix and not file_path.startswith(prefix):
                return False

            if suffix:
                remaining = file_path[len(prefix) :].lstrip("/")
                return fnmatch.fnmatch(remaining, f"*{suffix}") or fnmatch.fnmatch(
                    remaining, f"**/{suffix}"
                )

            return file_path.startswith(prefix) if prefix else True

    return fnmatch.fnmatch(file_path, pattern)


def get_deployment_order(
    affected: Set[str], order: WorkflowOrder
) -> List[List[str]]:
    """
    Get the deployment order for affected workflows.

    Returns workflows grouped by level, where each level can be deployed
    in parallel but must wait for previous levels to complete.

    Args:
        affected: Set of affected workflow names.
        order: WorkflowOrder configuration.

    Returns:
        List of lists, where each inner list contains workflows at that level.
        Empty list if no workflows are affected.
    """
    if not affected:
        return []

    # Group affected workflows by level
    levels_with_affected: Dict[int, List[str]] = defaultdict(list)

    for name in affected:
        if name in order.workflows:
            level = order.workflows[name].level
            levels_with_affected[level].append(name)

    # Sort by level and return
    result: List[List[str]] = []
    for level in sorted(levels_with_affected.keys()):
        result.append(sorted(levels_with_affected[level]))

    return result


def should_wait_for(
    workflow: str, completed: Set[str], order: WorkflowOrder
) -> Optional[str]:
    """
    Check if a workflow should wait for dependencies.

    Args:
        workflow: Name of the workflow to check.
        completed: Set of completed workflow names.
        order: WorkflowOrder configuration.

    Returns:
        Name of a dependency that isn't complete yet, or None if all deps are met.
    """
    if workflow not in order.workflows:
        return None

    config = order.workflows[workflow]

    # Check explicit dependencies
    for dep in config.depends_on:
        if dep not in completed:
            return dep

    # Check level-based dependencies (all workflows in lower levels must complete)
    for level in range(config.level):
        for other_workflow in order.levels[level]:
            if other_workflow not in completed:
                return other_workflow

    return None


def get_all_dependencies(workflow: str, order: WorkflowOrder) -> Set[str]:
    """
    Get all transitive dependencies for a workflow.

    Args:
        workflow: Name of the workflow.
        order: WorkflowOrder configuration.

    Returns:
        Set of all workflow names that must complete before this workflow.
    """
    if workflow not in order.workflows:
        return set()

    deps: Set[str] = set()
    config = order.workflows[workflow]

    # Add explicit dependencies and their transitive deps
    for dep in config.depends_on:
        deps.add(dep)
        deps.update(get_all_dependencies(dep, order))

    # Add all workflows from lower levels
    for level in range(config.level):
        for other_workflow in order.levels[level]:
            deps.add(other_workflow)

    return deps
