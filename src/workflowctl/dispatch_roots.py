#!/usr/bin/env python3
"""Dispatch root workflows to GitHub Actions.

This module handles dispatching root workflows with proper trigger_descendants
logic based on inputs, commit messages, and changed files.

Usage:
    python3 src/workflowctl/workflowctl.py dispatch-roots \
        --repo owner/repo \
        --roots "bootstrap\\nwww_shared" \
        --changed "file1.py" \
        --commit-message "feat: add feature" \
        --trigger-descendants false
"""
import argparse
import os
import re
import sys

from utils import (
    dispatch_gh_workflow,
    file_matches_pattern,
    get_all_descendants,
    load_graph_with_error,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dispatch root workflows to GitHub Actions"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository (owner/repo)"
    )
    parser.add_argument(
        "--roots",
        required=True,
        help="Newline-separated list of root workflow keys"
    )
    parser.add_argument(
        "--changed",
        default="",
        help="Newline-separated list of changed files"
    )
    parser.add_argument(
        "--commit-message",
        default=os.environ.get("COMMIT_MESSAGE", ""),
        help="The commit message to check for [trigger descendants]"
    )
    parser.add_argument(
        "--trigger-descendants",
        default="false",
        help="Input value for trigger_descendants (true/false)"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow-dependencies.json",
        help="Path to workflow dependency graph JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be dispatched without actually dispatching"
    )
    return parser.parse_args()


def _get_affected_workflows(
    changed_files: list[str],
    graph: dict
) -> set[str]:
    """Get workflows affected by changed files."""
    affected: set[str] = set()
    for workflow_key, workflow_config in graph.items():
        patterns = workflow_config.get("paths", [])
        for filepath in changed_files:
            if any(file_matches_pattern(filepath, p) for p in patterns):
                affected.add(workflow_key)
                break
    return affected


def _descendants_have_changes(
    roots: list[str],
    changed_files: list[str],
    graph: dict
) -> bool:
    """Check if any descendant of the roots has changed files."""
    affected = _get_affected_workflows(changed_files, graph)

    # Get all descendants of all roots
    all_descendants: set[str] = set()
    cache: dict[str, set[str]] = {}
    for root in roots:
        all_descendants.update(get_all_descendants(root, graph, cache))

    # Check if any affected workflow is a descendant
    return bool(affected & all_descendants)


def should_trigger_descendants(
    trigger_input: str,
    commit_message: str,
    changed_files: list[str],
    roots: list[str],
    graph: dict | None
) -> bool:
    """Determine if descendants should be triggered.

    Returns True if:
    1. trigger_descendants input is "true", OR
    2. Commit message contains [trigger descendants], OR
    3. etc/workflow-dependencies.json was changed, OR
    4. Any descendant workflow also has changed files
    """
    # Check input
    if trigger_input.lower() == "true":
        return True

    # Check commit message
    if re.search(r"\[trigger descendants\]", commit_message, re.IGNORECASE):
        return True

    # Check if workflow-dependencies.json changed
    if "etc/workflow-dependencies.json" in changed_files:
        return True

    # Check if any descendants also have changed files
    if graph and _descendants_have_changes(roots, changed_files, graph):
        return True

    return False


def workflow_file_exists(workflow: str) -> bool:
    """Check if the workflow file exists."""
    workflow_file = f".github/workflows/{workflow}.yml"
    return os.path.isfile(workflow_file)


def workflow_accepts_trigger_descendants(workflow: str) -> bool:
    """Check if a workflow accepts the trigger_descendants input."""
    workflow_file = f".github/workflows/{workflow}.yml"
    try:
        with open(workflow_file, encoding="utf-8") as f:
            content = f.read()
            return "trigger_descendants:" in content
    except (OSError, IOError):
        return False


def dispatch_workflow(
    workflow: str,
    repo: str,
    trigger_descendants: bool,
    dry_run: bool
) -> bool:
    """Dispatch a single workflow. Returns True on success."""
    workflow_file = f".github/workflows/{workflow}.yml"

    if dry_run:
        flag_msg = " (with trigger_descendants=true)" if trigger_descendants else ""
        print(f"  [DRY RUN] Would dispatch: {workflow_file}{flag_msg}")
        return True

    print(f"  Dispatching: {workflow_file}")

    extra_args = None
    if trigger_descendants and workflow_accepts_trigger_descendants(workflow):
        extra_args = ["-f", "trigger_descendants=true"]
    elif trigger_descendants:
        print("    (workflow does not accept trigger_descendants)")

    success = dispatch_gh_workflow(workflow_file, repo, extra_args)
    if success:
        print(f"    Successfully dispatched {workflow}.yml")
    return success


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse roots
    roots = [r.strip() for r in args.roots.split("\n") if r.strip()]

    if not roots:
        print("No workflows to dispatch")
        return 0

    # Parse changed files
    changed_files = [f.strip() for f in args.changed.split("\n") if f.strip()]

    # Load graph for descendant checking
    graph, error = load_graph_with_error(args.graph)
    if error:
        print(f"Warning: {error} - descendant detection disabled", file=sys.stderr)

    # Determine if we should trigger descendants
    trigger = should_trigger_descendants(
        args.trigger_descendants,
        args.commit_message,
        changed_files,
        roots,
        graph
    )

    if trigger:
        print("Trigger descendants: enabled")
    else:
        print("Trigger descendants: disabled (default)")

    print(f"Dispatching {len(roots)} root workflow(s)...")

    # Dispatch each root
    dispatched = 0
    failed = 0

    for workflow in roots:
        if not workflow_file_exists(workflow):
            print(f"  Warning: {workflow}.yml not found, skipping")
            continue

        if dispatch_workflow(workflow, args.repo, trigger, args.dry_run):
            dispatched += 1
        else:
            failed += 1

    print(f"\nDispatched: {dispatched}, Failed: {failed}")

    if trigger:
        print("Note: Descendants will be triggered via trigger_descendants")
    else:
        print("Descendants NOT triggered (default behavior)")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
