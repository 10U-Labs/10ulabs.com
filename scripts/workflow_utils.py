#!/usr/bin/env python3
"""Shared utilities for workflow orchestration scripts.

This module provides common functions used across multiple orchestration scripts
to avoid code duplication.
"""
import json
import subprocess
from typing import Any


def load_dependency_graph(graph_path: str) -> dict[str, Any]:
    """Load the workflow dependency graph from JSON file."""
    with open(graph_path, encoding="utf-8") as f:
        return json.load(f)


def build_name_to_key_map(graph: dict[str, Any]) -> dict[str, str]:
    """Build a mapping from workflow display names to workflow keys.

    This is used to map the workflow names returned by GitHub API
    to the workflow keys used in the dependency graph.
    """
    name_to_key: dict[str, str] = {}
    for key, config in graph.items():
        name = config.get("name", "")
        if name:
            name_to_key[name] = key
    return name_to_key


def get_all_descendants(
    workflow: str, graph: dict[str, Any], cache: dict[str, set[str]] | None = None
) -> set[str]:
    """Get all descendants (workflows that depend on this one) of a workflow.

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


def get_workflow_runs(repo: str, status: str) -> list[dict[str, Any]]:
    """Query GitHub API for workflow runs with the given status.

    Args:
        repo: The GitHub repository (e.g., 'owner/repo')
        status: The workflow run status to filter by (e.g., 'in_progress', 'queued')

    Returns:
        List of workflow run objects from the API
    """
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/actions/runs",
            "-q", f".workflow_runs | map(select(.status == \"{status}\"))"
        ],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []
