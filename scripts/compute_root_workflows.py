#!/usr/bin/env python3
"""
Compute root workflows and execution plans based on changed files.

This script reads the workflow dependency graph from etc/workflow-dependencies.yml
and determines which workflows should be triggered for a given set of changed files.

A "root" workflow is one whose files were modified but has no ancestors that were
also modified. The execution plan includes the root workflow(s) and all their
descendants in topological order (dependencies before dependents).

Usage:
    python3 scripts/compute_root_workflows.py <changed_files>
    python3 scripts/compute_root_workflows.py --execution-plan <changed_files>

    Where <changed_files> is a newline-separated list of file paths.

Output:
    Default: JSON array of root workflow keys, e.g., ["bootstrap"]
    With --execution-plan: JSON array of all workflows to run in order
"""

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def load_dependency_graph(graph_path: Path) -> dict[str, Any]:
    """Load the workflow dependency graph from YAML file."""
    with open(graph_path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_and_validate_graph(graph_arg: str) -> dict[str, Any]:
    """Load dependency graph from path, exiting with error if not found."""
    graph_path = Path(graph_arg)
    if not graph_path.exists():
        print(f"Error: Dependency graph not found at {graph_path}", file=sys.stderr)
        sys.exit(1)
    return load_dependency_graph(graph_path)


def get_all_ancestors(
    workflow: str, graph: dict[str, Any], cache: dict[str, set[str]] | None = None
) -> set[str]:
    """
    Get all ancestors (transitive dependencies) of a workflow.

    Returns a set of workflow keys that this workflow depends on,
    including indirect dependencies.
    """
    if cache is None:
        cache = {}

    if workflow in cache:
        return cache[workflow]

    ancestors: set[str] = set()
    direct_deps = graph.get(workflow, {}).get("depends_on", [])

    for dep in direct_deps:
        ancestors.add(dep)
        ancestors.update(get_all_ancestors(dep, graph, cache))

    cache[workflow] = ancestors
    return ancestors


def get_all_descendants(
    workflow: str, graph: dict[str, Any], cache: dict[str, set[str]] | None = None
) -> set[str]:
    """
    Get all descendants (workflows that depend on this one) of a workflow.

    Returns a set of workflow keys that depend on this workflow,
    including indirect dependents.
    """
    if cache is None:
        cache = {}

    if workflow in cache:
        return cache[workflow]

    descendants: set[str] = set()

    # Find all workflows that directly depend on this one
    for wf_key, wf_config in graph.items():
        if workflow in wf_config.get("depends_on", []):
            descendants.add(wf_key)
            descendants.update(get_all_descendants(wf_key, graph, cache))

    cache[workflow] = descendants
    return descendants


def _insert_sorted(queue: list[str], item: str) -> None:
    """Insert an item into a sorted list maintaining sort order."""
    for i, existing in enumerate(queue):
        if item < existing:
            queue.insert(i, item)
            return
    queue.append(item)


def topological_sort(workflows: set[str], graph: dict[str, Any]) -> list[str]:
    """
    Sort workflows in topological order (dependencies before dependents).

    Uses Kahn's algorithm to ensure workflows are ordered such that
    all dependencies come before their dependents.
    """
    # Build in-degree map (only for workflows in our set)
    in_degree: dict[str, int] = {wf: 0 for wf in workflows}
    for wf in workflows:
        for dep in graph.get(wf, {}).get("depends_on", []):
            if dep in workflows:
                in_degree[wf] += 1

    # Start with workflows that have no dependencies (in our set)
    queue = sorted([wf for wf, degree in in_degree.items() if degree == 0])
    result: list[str] = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        # Find workflows that depend on current and add ready ones to queue
        for wf in workflows:
            if current in graph.get(wf, {}).get("depends_on", []):
                in_degree[wf] -= 1
                if in_degree[wf] == 0:
                    _insert_sorted(queue, wf)

    return result


def compute_execution_plan(roots: list[str], graph: dict[str, Any]) -> list[str]:
    """
    Compute the full execution plan starting from root workflows.

    Returns all workflows that need to run (roots + all descendants)
    in topological order.
    """
    # Collect all workflows to run (roots + their descendants)
    all_workflows: set[str] = set(roots)
    descendant_cache: dict[str, set[str]] = {}

    for root in roots:
        all_workflows.update(get_all_descendants(root, graph, descendant_cache))

    # Sort in topological order
    return topological_sort(all_workflows, graph)


def file_matches_patterns(filepath: str, patterns: list[str]) -> bool:
    """Check if a file path matches any of the given glob patterns."""
    for pattern in patterns:
        # Handle ** patterns for directory matching
        if "**" in pattern:
            # Convert glob pattern to work with fnmatch
            # e.g., "src/bootstrap/**" matches "src/bootstrap/main.tf"
            base_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(filepath, base_pattern):
                return True
            # Also check if file is under the directory
            dir_prefix = pattern.split("**")[0]
            if filepath.startswith(dir_prefix):
                return True
        elif fnmatch.fnmatch(filepath, pattern):
            return True
    return False


def get_affected_workflows(
    changed_files: list[str], graph: dict[str, Any]
) -> set[str]:
    """
    Determine which workflows are affected by the changed files.

    Returns a set of workflow keys whose path patterns match any changed file.
    """
    affected: set[str] = set()

    for workflow_key, workflow_config in graph.items():
        patterns = workflow_config.get("paths", [])
        for filepath in changed_files:
            if file_matches_patterns(filepath, patterns):
                affected.add(workflow_key)
                break

    return affected


def compute_root_workflows(
    changed_files: list[str], graph: dict[str, Any]
) -> list[str]:
    """
    Compute the root workflows to trigger.

    A root workflow is one that:
    1. Has files that were modified (affected)
    2. Has NO ancestors that were also affected

    Root workflows should be triggered directly. Their descendants will be
    triggered via workflow_run cascading when the roots complete.
    """
    affected = get_affected_workflows(changed_files, graph)

    if not affected:
        return []

    # Build ancestor cache
    ancestor_cache: dict[str, set[str]] = {}
    for workflow in affected:
        get_all_ancestors(workflow, graph, ancestor_cache)

    # Find roots: affected workflows with no affected ancestors
    roots: list[str] = []
    for workflow in affected:
        ancestors = ancestor_cache.get(workflow, set())
        # If none of this workflow's ancestors are affected, it's a root
        if not ancestors.intersection(affected):
            roots.append(workflow)

    # Sort for deterministic output
    return sorted(roots)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute root workflows to trigger based on changed files."
    )
    parser.add_argument(
        "changed_files",
        nargs="?",
        default="-",
        help="Newline-separated list of changed files (or - for stdin)",
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow-dependencies.yml",
        help="Path to workflow dependency graph YAML file",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "lines"],
        default="json",
        help="Output format: json array or newline-separated lines",
    )
    parser.add_argument(
        "--execution-plan",
        action="store_true",
        help="Output full execution plan (roots + descendants) in topological order",
    )
    parser.add_argument(
        "--start-from",
        help="Specify a workflow to start from (bypasses file detection)",
    )
    parser.add_argument(
        "--slots",
        type=int,
        default=0,
        help="Output slot variables for GitHub Actions (key_01, key_02, ... up to N)",
    )
    return parser.parse_args()


def _output_slots(output: list[str], num_slots: int) -> None:
    """Output slot variables for GitHub Actions."""
    print(f"count={len(output)}")
    for i in range(1, num_slots + 1):
        key = output[i - 1] if i <= len(output) else ""
        print(f"key_{i:02d}={key}")


def _output_results(output: list[str], output_format: str) -> None:
    """Output results in the specified format."""
    if output_format == "json":
        print(json.dumps(output))
    else:
        for item in output:
            print(item)


def main() -> None:
    """Main entry point."""
    args = _parse_args()

    # Read changed files
    changed_files_str = (
        sys.stdin.read() if args.changed_files == "-" else args.changed_files
    )
    changed_files = [
        line.strip() for line in changed_files_str.strip().split("\n") if line.strip()
    ]

    # Load dependency graph
    graph = load_and_validate_graph(args.graph)

    # Determine roots: either from --start-from or from changed files
    if args.start_from:
        if args.start_from not in graph:
            print(f"Error: Unknown workflow '{args.start_from}'", file=sys.stderr)
            print(
                f"Available workflows: {', '.join(sorted(graph.keys()))}",
                file=sys.stderr,
            )
            sys.exit(1)
        roots = [args.start_from]
    else:
        roots = compute_root_workflows(changed_files, graph)

    # Compute execution plan if requested
    output = (
        compute_execution_plan(roots, graph)
        if args.execution_plan or args.slots > 0
        else roots
    )

    # Output results
    if args.slots > 0:
        _output_slots(output, args.slots)
    else:
        _output_results(output, args.output_format)


if __name__ == "__main__":
    main()
