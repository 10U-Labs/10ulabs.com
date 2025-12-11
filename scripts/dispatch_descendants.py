#!/usr/bin/env python3
"""Dispatch all workflows that depend on the completed workflow.

This script reads the workflow dependency graph and dispatches all workflows
that list the specified workflow as a dependency. For workflows with multiple
dependencies, it checks that all other dependencies have completed successfully
before dispatching (fan-in behavior).

Usage:
    python3 scripts/dispatch_descendants.py --workflow bootstrap --repo owner/repo
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dispatch descendant workflows after a workflow completes"
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="The workflow key that just completed (e.g., 'bootstrap')"
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
        "--dry-run",
        action="store_true",
        help="Print what would be dispatched without actually dispatching"
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Hours to look back for successful dependency runs (default: 24)"
    )
    parser.add_argument(
        "--skip-descendants",
        action="store_true",
        help="Pass skip_descendants=true to dispatched workflows"
    )
    return parser.parse_args()


def load_dependency_graph(graph_path: str) -> dict:
    """Load the workflow dependency graph from JSON."""
    with open(graph_path, encoding="utf-8") as f:
        return json.load(f)


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
    dry_run: bool,
    skip_descendants: bool = False
) -> bool:
    """Dispatch a single workflow. Returns True on success."""
    workflow_file = f".github/workflows/{workflow}.yml"
    if dry_run:
        skip_flag = " (with skip_descendants=true)" if skip_descendants else ""
        print(f"  [DRY RUN] Would dispatch: {workflow_file}{skip_flag}")
        return True

    print(f"  Dispatching: {workflow_file}")
    cmd = ["gh", "workflow", "run", workflow_file, "--repo", repo]
    if skip_descendants:
        cmd.extend(["-f", "skip_descendants=true"])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        print(f"    Error: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main() -> int:
    """Main entry point."""
    args = parse_args()

    graph = load_dependency_graph(args.graph)
    descendants = find_descendants(graph, args.workflow)

    if not descendants:
        print(f"No descendants found for workflow: {args.workflow}")
        return 0

    print(f"Found {len(descendants)} descendant(s) of '{args.workflow}':")
    for desc in descendants:
        deps = graph.get(desc, {}).get("depends_on", [])
        print(f"  - {desc} (depends on: {', '.join(deps)})")
    print()

    dispatched = 0
    skipped = 0

    for descendant in descendants:
        deps = graph.get(descendant, {}).get("depends_on", [])

        if len(deps) == 1:
            # Single dependency - dispatch immediately
            print(f"{descendant}: single dependency, dispatching...")
            if dispatch_workflow(
                descendant, args.repo, args.dry_run, args.skip_descendants
            ):
                dispatched += 1
        else:
            # Multiple dependencies - check if all are met
            print(f"{descendant}: checking {len(deps)} dependencies...")
            all_met, missing = all_dependencies_met(
                graph, descendant, args.workflow, args.repo, args.lookback_hours
            )
            if all_met:
                print("  All dependencies met, dispatching...")
                if dispatch_workflow(
                    descendant, args.repo, args.dry_run, args.skip_descendants
                ):
                    dispatched += 1
            else:
                print(f"  Waiting for: {', '.join(missing)}")
                skipped += 1

    print(f"\nDispatched: {dispatched}, Waiting: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
