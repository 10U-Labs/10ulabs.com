#!/usr/bin/env python3
"""
Execute a workflow plan sequentially.

This script takes a JSON array of workflow keys and executes each workflow
in order, waiting for completion before moving to the next.

Usage:
    python3 scripts/execute_workflow_plan.py --plan '["bootstrap", "www_shared"]'

Environment variables:
    GH_TOKEN: GitHub token for authentication (required)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml


def run_gh(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a gh command and return the result."""
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True,
        text=True,
        check=False
    )
    return result


def get_latest_run_id(workflow_file: str) -> str | None:
    """Get the ID of the most recent run for a workflow."""
    result = run_gh(
        "run", "list",
        "--workflow", workflow_file,
        "--limit", "1",
        "--json", "databaseId",
        "--jq", ".[0].databaseId"
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def wait_for_completion(
    run_id: str,
    workflow_name: str,
    timeout_minutes: int = 60
) -> tuple[bool, str]:
    """Wait for a workflow run to complete."""
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    poll_interval = 30  # seconds

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            print(f"  Timeout waiting for {workflow_name}")
            return False, "timeout"

        result = run_gh(
            "run", "view", run_id,
            "--json", "status,conclusion",
            "--jq", "[.status, .conclusion] | @tsv"
        )

        if result.returncode != 0:
            print(f"  Error checking status: {result.stderr}")
            time.sleep(poll_interval)
            continue

        parts = result.stdout.strip().split("\t")
        status = parts[0] if parts else ""
        conclusion = parts[1] if len(parts) > 1 else ""

        if status == "completed":
            return conclusion == "success", conclusion

        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        print(f"  [{mins:02d}:{secs:02d}] Status: {status}")
        time.sleep(poll_interval)

    return False, "unknown"


def load_dependency_graph(graph_path: Path) -> dict[str, Any]:
    """Load the workflow dependency graph from YAML file."""
    with open(graph_path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def execute_plan(
    plan: list[str],
    graph: dict[str, Any],
    github_hosted: bool = False
) -> list[str]:
    """
    Execute workflows in the plan sequentially.

    Returns a list of failed workflow keys.
    """
    # ECS on-demand workflows (no github_hosted support)
    ecs_on_demand = {"contact", "echo", "rack_designer", "www_index"}

    print(f"Executing {len(plan)} workflows in sequence:")
    for i, wf in enumerate(plan, 1):
        print(f"  {i}. {graph[wf]['name']}")
    print()

    failed_workflows: list[str] = []

    for i, workflow_key in enumerate(plan, 1):
        workflow_file = f".github/workflows/{workflow_key}.yml"
        workflow_name = graph[workflow_key]["name"]

        print(f"[{i}/{len(plan)}] {workflow_name}")
        print(f"  File: {workflow_file}")

        # Dispatch the workflow
        cmd = ["workflow", "run", workflow_file]
        if github_hosted and workflow_key not in ecs_on_demand:
            cmd.extend(["--field", "github_hosted=true"])

        result = run_gh(*cmd)
        if result.returncode != 0:
            print(f"  Failed to dispatch: {result.stderr}")
            failed_workflows.append(workflow_key)
            continue

        # Wait a moment for the run to be registered
        time.sleep(5)

        # Get the run ID
        run_id = get_latest_run_id(workflow_file)
        if not run_id:
            print("  Could not find run ID")
            failed_workflows.append(workflow_key)
            continue

        print(f"  Run ID: {run_id}")
        print("  Waiting for completion...")

        # Wait for completion
        success, conclusion = wait_for_completion(run_id, workflow_name)

        if success:
            print("  Completed successfully")
        else:
            print(f"  Failed with conclusion: {conclusion}")
            failed_workflows.append(workflow_key)
            # Stop on first failure
            print(f"\nStopping execution due to failure in {workflow_name}")
            break

        print()

    return failed_workflows


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute a workflow plan sequentially."
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="JSON array of workflow keys to execute"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow-dependencies.yml",
        help="Path to workflow dependency graph YAML file"
    )
    parser.add_argument(
        "--github-hosted",
        action="store_true",
        help="Use GitHub-hosted runners"
    )

    args = parser.parse_args()

    # Verify GH_TOKEN is set
    if not os.environ.get("GH_TOKEN"):
        print("Error: GH_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)

    # Load plan
    try:
        plan = json.loads(args.plan)
    except json.JSONDecodeError as e:
        print(f"Error parsing plan JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not plan:
        print("No workflows to execute")
        return

    # Load dependency graph
    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(f"Error: Dependency graph not found at {graph_path}", file=sys.stderr)
        sys.exit(1)

    graph = load_dependency_graph(graph_path)

    # Execute plan
    failed = execute_plan(plan, graph, args.github_hosted)

    # Summary
    if failed:
        print(f"\nFailed workflows: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"\nAll {len(plan)} workflows completed successfully!")


if __name__ == "__main__":
    main()
