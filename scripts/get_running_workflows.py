#!/usr/bin/env python3
"""Get currently running workflows from GitHub Actions.

This script queries the GitHub API for workflow runs that are in_progress or queued,
maps them to workflow keys using the dependency graph, and outputs a JSON array
of workflow keys.

Usage:
    python3 scripts/get_running_workflows.py --repo owner/repo

Output:
    JSON array of workflow keys, e.g., ["api_backend", "www_shared"]
"""
import argparse
import json
import sys

from workflow_utils import (
    build_name_to_key_map,
    get_workflow_runs,
    load_dependency_graph,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Get currently running workflows from GitHub Actions"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="The GitHub repository (e.g., 'owner/repo')"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow-dependencies.json",
        help="Path to the workflow dependency graph file"
    )
    parser.add_argument(
        "--exclude-orchestrator",
        action="store_true",
        default=True,
        help="Exclude the orchestrator workflow from results (default: true)"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load dependency graph
    try:
        graph = load_dependency_graph(args.graph)
    except FileNotFoundError:
        print(f"Error: Graph file not found: {args.graph}", file=sys.stderr)
        return 1

    # Build name-to-key mapping
    name_to_key = build_name_to_key_map(graph)

    # Get in_progress and queued workflow runs
    in_progress = get_workflow_runs(args.repo, "in_progress")
    queued = get_workflow_runs(args.repo, "queued")

    # Combine and extract unique workflow names
    all_runs = in_progress + queued
    workflow_names = set()
    for run in all_runs:
        name = run.get("name", "")
        if name:
            workflow_names.add(name)

    # Map names to keys
    workflow_keys: list[str] = []
    for name in workflow_names:
        if name in name_to_key:
            key = name_to_key[name]
            # Optionally exclude orchestrator
            if args.exclude_orchestrator and key == "orchestrator":
                continue
            workflow_keys.append(key)

    # Sort for deterministic output
    workflow_keys.sort()

    # Output as JSON array
    print(json.dumps(workflow_keys))
    return 0


if __name__ == "__main__":
    sys.exit(main())
