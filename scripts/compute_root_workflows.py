#!/usr/bin/env python3
"""
Compute root workflows to trigger based on changed files.

This script reads the workflow dependency graph from etc/workflow-dependencies.yml
and determines which workflows should be triggered for a given set of changed files.

A "root" workflow is one whose files were modified but has no ancestors that were
also modified. Root workflows should be triggered directly; their descendants will
be triggered via workflow_run cascading.

Usage:
    python3 scripts/compute_root_workflows.py <changed_files>

    Where <changed_files> is a newline-separated list of file paths.

Output:
    JSON array of workflow keys to trigger, e.g., ["bootstrap", "api"]
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


def main() -> None:
    """Main entry point."""
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

    args = parser.parse_args()

    # Read changed files
    if args.changed_files == "-":
        changed_files_str = sys.stdin.read()
    else:
        changed_files_str = args.changed_files

    changed_files = [
        line.strip() for line in changed_files_str.strip().split("\n") if line.strip()
    ]

    # Load dependency graph
    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(f"Error: Dependency graph not found at {graph_path}", file=sys.stderr)
        sys.exit(1)

    graph = load_dependency_graph(graph_path)

    # Compute root workflows
    roots = compute_root_workflows(changed_files, graph)

    # Output results
    if args.output_format == "json":
        print(json.dumps(roots))
    else:
        for root in roots:
            print(root)


if __name__ == "__main__":
    main()
