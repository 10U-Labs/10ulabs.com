#!/usr/bin/env python3
"""Dispatch root workflows to GitHub Actions.

This module handles dispatching root workflows with proper trigger_descendants
and invalidate_cloudfront logic based on inputs, commit messages, and changed files.

Usage:
    python3 src/workflowctl/workflowctl.py dispatch-root-workflows \
        --repo owner/repo \
        --changed-files "file1.py,file2.py" \
        --running '["www_shared"]' \
        --trigger-descendants \
        --invalidate-cloudfront

Exit codes:
    0: Success (all dispatches succeeded or nothing to dispatch)
    1: Failure (at least one dispatch failed)

No stdout output. Errors go to stderr.
"""
import argparse
import os
import re
import sys

from compute_roots import compute_merge_roots, load_graph_and_compute_roots
from utils import (
    add_changed_files_arg,
    add_running_arg,
    dispatch_gh_workflow,
    file_matches_pattern,
    get_all_descendants,
    parse_changed_files,
    parse_running_workflows,
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
    add_changed_files_arg(parser)
    add_running_arg(parser)
    parser.add_argument(
        "--commit-message",
        default=os.environ.get("COMMIT_MESSAGE", ""),
        help="The commit message to check for [trigger descendants] or [invalidate cloudfront]"
    )
    parser.add_argument(
        "--trigger-descendants",
        action="store_true",
        help="Trigger descendant workflows after root workflows complete"
    )
    parser.add_argument(
        "--invalidate-cloudfront",
        action="store_true",
        help="Force CloudFront cache invalidation in descendant workflows"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow-dependencies.json",
        help="Path to workflow dependency graph JSON file"
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
    trigger_flag: bool,
    commit_message: str,
    changed_files: list[str],
    roots: list[str],
    graph: dict | None
) -> bool:
    """Determine if descendants should be triggered.

    Returns True if:
    1. trigger_flag is True (--trigger-descendants passed), OR
    2. Commit message contains [trigger descendants], OR
    3. etc/workflow-dependencies.json was changed, OR
    4. Any descendant workflow also has changed files
    """
    if trigger_flag:
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


def should_invalidate_cloudfront(
    invalidate_flag: bool,
    commit_message: str
) -> bool:
    """Determine if CloudFront cache should be invalidated.

    Returns True if:
    1. invalidate_flag is True (--invalidate-cloudfront passed), OR
    2. Commit message contains [invalidate cloudfront]
    """
    if invalidate_flag:
        return True

    if re.search(r"\[invalidate cloudfront\]", commit_message, re.IGNORECASE):
        return True

    return False


def workflow_file_exists(workflow: str) -> bool:
    """Check if the workflow file exists."""
    workflow_file = f".github/workflows/{workflow}.yml"
    return os.path.isfile(workflow_file)


def workflow_accepts_input(workflow: str, input_name: str) -> bool:
    """Check if a workflow accepts a specific input."""
    workflow_file = f".github/workflows/{workflow}.yml"
    try:
        with open(workflow_file, encoding="utf-8") as f:
            content = f.read()
            return f"{input_name}:" in content
    except (OSError, IOError):
        return False


def dispatch_workflow(
    workflow: str,
    repo: str,
    trigger_descendants: bool,
    invalidate_cloudfront: bool
) -> bool:
    """Dispatch a single workflow. Returns True on success."""
    workflow_file = f".github/workflows/{workflow}.yml"

    # Build list of flags to pass
    flags: list[str] = []
    if trigger_descendants and workflow_accepts_input(workflow, "trigger_descendants"):
        flags.extend(["-f", "trigger_descendants=true"])
    if invalidate_cloudfront and workflow_accepts_input(workflow, "invalidate_cloudfront"):
        flags.extend(["-f", "invalidate_cloudfront=true"])

    extra_args = flags if flags else None
    return dispatch_gh_workflow(workflow_file, repo, extra_args)


def main() -> int:
    """Main entry point."""
    args = parse_args()
    changed_files = parse_changed_files(args.changed_files)

    graph, roots, error = load_graph_and_compute_roots(args.graph, changed_files)
    if error or graph is None:
        print(error, file=sys.stderr)
        return 1

    running_workflows, error = parse_running_workflows(args.running)
    if error:
        print(error, file=sys.stderr)
        return 1

    if running_workflows:
        roots = compute_merge_roots(running_workflows, roots, graph)

    if not roots:
        return 0

    # Determine if we should trigger descendants
    trigger = should_trigger_descendants(
        args.trigger_descendants,
        args.commit_message,
        changed_files,
        roots,
        graph
    )

    # Determine if we should invalidate CloudFront
    invalidate = should_invalidate_cloudfront(
        args.invalidate_cloudfront,
        args.commit_message
    )

    # Dispatch each root
    failed = 0
    for workflow in roots:
        if not workflow_file_exists(workflow):
            continue
        if not dispatch_workflow(workflow, args.repo, trigger, invalidate):
            failed += 1

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
