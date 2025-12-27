#!/usr/bin/env python3
"""Dispatch all workflows that depend on the completed workflow.

This script reads the workflow dependency graph and dispatches all workflows
that list the specified workflow as a dependency. For workflows with multiple
dependencies, it checks that all other dependencies have completed successfully
before dispatching (fan-in behavior).

Usage:
    python3 src/workflowctl/workflowctl.py dispatch-descendant-workflows \
        --workflow bootstrap --repo owner/repo \
        --trigger-descendants --invalidate-cloudfront

Exit codes:
    0: Success (all dispatches succeeded or nothing to dispatch)
    1: Failure (at least one dispatch failed)

No stdout output. Errors go to stderr.
"""
import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from utils import create_base_parser, dispatch_gh_workflow, load_dependency_graph


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_base_parser(
        "Dispatch descendant workflows after a workflow completes"
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="The workflow key that just completed (e.g., 'bootstrap')"
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Hours to look back for successful dependency runs (default: 24)"
    )
    parser.add_argument(
        "--trigger-descendants",
        action="store_true",
        help="Pass trigger_descendants=true to dispatched workflows"
    )
    parser.add_argument(
        "--invalidate-cloudfront",
        action="store_true",
        help="Pass invalidate_cloudfront=true to dispatched workflows"
    )
    return parser.parse_args()


def find_descendants(graph: dict, workflow: str) -> list[str]:
    """Find all workflows that directly depend on the specified workflow."""
    return [
        name for name, config in graph.items()
        if workflow in config.get("depends_on", [])
    ]


def get_workflow_name(graph: dict, workflow_key: str) -> str:
    """Get the display name for a workflow from the graph."""
    return graph.get(workflow_key, {}).get("name", workflow_key)


def check_workflow_completed(
    workflow_name: str,
    repo: str,
    since: datetime
) -> bool:
    """Check if a workflow has completed successfully since the given time."""
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/actions/runs",
            "-q", f'.workflow_runs[] | select(.name == "{workflow_name}" and '
                  f'.conclusion == "success" and .created_at >= "{since_str}") '
                  f'| .id',
        ],
        capture_output=True,
        text=True,
        check=False
    )
    # If we got any output, there's at least one successful run
    return bool(result.stdout.strip())


def all_dependencies_met(
    graph: dict,
    descendant: str,
    current_workflow: str,
    repo: str,
    lookback_hours: int
) -> tuple[bool, list[str]]:
    """Check if all dependencies for a descendant have been met.

    Returns (all_met, missing_dependencies).
    The current_workflow is assumed to have just completed successfully.
    """
    dependencies = graph.get(descendant, {}).get("depends_on", [])
    other_deps = [d for d in dependencies if d != current_workflow]

    if not other_deps:
        return True, []

    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    missing = []

    for dep in other_deps:
        dep_name = get_workflow_name(graph, dep)
        if not check_workflow_completed(dep_name, repo, since):
            missing.append(dep)

    return len(missing) == 0, missing


def dispatch_workflow(
    workflow: str,
    repo: str,
    trigger_descendants: bool = False,
    invalidate_cloudfront: bool = False
) -> bool:
    """Dispatch a single workflow. Returns True on success."""
    workflow_file = f".github/workflows/{workflow}.yml"

    # Build list of flags to pass
    flags: list[str] = []
    if trigger_descendants:
        flags.extend(["-f", "trigger_descendants=true"])
    if invalidate_cloudfront:
        flags.extend(["-f", "invalidate_cloudfront=true"])

    extra_args = flags if flags else None
    return dispatch_gh_workflow(workflow_file, repo, extra_args)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    graph = load_dependency_graph(args.graph)
    descendants = find_descendants(graph, args.workflow)

    if not descendants:
        return 0

    failed = 0
    for descendant in descendants:
        deps = graph.get(descendant, {}).get("depends_on", [])

        if len(deps) == 1:
            # Single dependency - dispatch immediately
            if not dispatch_workflow(
                descendant, args.repo,
                args.trigger_descendants, args.invalidate_cloudfront
            ):
                failed += 1
        else:
            # Multiple dependencies - check if all are met
            all_met, _ = all_dependencies_met(
                graph, descendant, args.workflow, args.repo, args.lookback_hours
            )
            if all_met:
                if not dispatch_workflow(
                    descendant, args.repo,
                    args.trigger_descendants, args.invalidate_cloudfront
                ):
                    failed += 1
            # If not all met, skip (not a failure, just waiting)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
