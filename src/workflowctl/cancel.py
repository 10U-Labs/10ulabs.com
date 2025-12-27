#!/usr/bin/env python3
"""Cancel superseded workflow runs.

This script cancels workflow runs that will be re-run from the merge roots.
It identifies which running workflows are downstream of (or equal to) the
merge roots and cancels them.

Usage:
    python3 src/workflowctl/workflowctl.py cancel-workflows \
        --repo owner/repo \
        --merge-roots '["www_shared"]' \
        --graph etc/workflow-dependencies.json

Exit codes:
    0: Success (all cancellations succeeded or nothing to cancel)
    1: Failure (error occurred)

No stdout output. Errors go to stderr.
"""
import argparse
import json
import subprocess
import sys
from typing import Any

from utils import (
    build_name_to_key_map,
    create_base_parser,
    get_all_descendants,
    get_workflow_runs,
    load_graph_with_error,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_base_parser("Cancel superseded workflow runs")
    parser.add_argument(
        "--merge-roots",
        required=True,
        help="JSON array of merge root workflow keys"
    )
    return parser.parse_args()


def get_workflows_to_cancel(
    merge_roots: list[str], graph: dict[str, Any]
) -> set[str]:
    """Get all workflows that should be canceled (merge roots + descendants)."""
    to_cancel: set[str] = set(merge_roots)
    descendant_cache: dict[str, set[str]] = {}

    for root in merge_roots:
        to_cancel.update(get_all_descendants(root, graph, descendant_cache))

    return to_cancel


def get_cancelable_runs(repo: str, status: str) -> list[dict[str, Any]]:
    """Get workflow runs that can be canceled with additional fields."""
    runs = get_workflow_runs(repo, status)
    # Extract only the fields we need
    return [
        {"id": run.get("id"), "name": run.get("name"), "run_number": run.get("run_number")}
        for run in runs
    ]


def cancel_run(repo: str, run_id: int) -> bool:
    """Cancel a workflow run. Returns True on success."""
    result = subprocess.run(
        ["gh", "run", "cancel", str(run_id), "--repo", repo],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        # Run may have already completed - this is not an error
        if "cannot be cancelled" in result.stderr.lower():
            return True
        print(f"Failed to cancel run {run_id}: {result.stderr.strip()}",
              file=sys.stderr)
        return False
    return True


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse merge roots
    try:
        merge_roots = json.loads(args.merge_roots)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON for merge-roots: {args.merge_roots}",
              file=sys.stderr)
        return 1

    if not merge_roots:
        return 0

    # Load dependency graph
    graph, error = load_graph_with_error(args.graph)
    if graph is None:
        print(error, file=sys.stderr)
        return 1

    # Get workflows to cancel (merge roots + all descendants)
    workflows_to_cancel = get_workflows_to_cancel(merge_roots, graph)

    # Build name-to-key mapping
    name_to_key = build_name_to_key_map(graph)

    # Get cancelable runs and filter to ones that should be canceled
    runs_to_cancel: list[dict[str, Any]] = [
        run for run in (get_cancelable_runs(args.repo, "in_progress") +
                        get_cancelable_runs(args.repo, "queued"))
        if name_to_key.get(run.get("name", "")) in workflows_to_cancel
    ]

    if not runs_to_cancel:
        return 0

    # Cancel runs
    failed = 0
    for run in runs_to_cancel:
        if not cancel_run(args.repo, run["id"]):
            failed += 1

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
