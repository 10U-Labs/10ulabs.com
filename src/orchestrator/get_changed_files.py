#!/usr/bin/env python3
"""Get changed files between two git commits.

This module handles edge cases like force pushes, shallow clones, and
initial commits to reliably determine which files changed.

Usage:
    python3 src/orchestrator/orchestrator.py get-changed-files \
        --base <base_sha> --head <head_sha>
"""
import argparse
import sys

from utils import run_subprocess


ZERO_SHA = "0000000000000000000000000000000000000000"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Get changed files between two git commits"
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base commit SHA (before)"
    )
    parser.add_argument(
        "--head",
        required=True,
        help="Head commit SHA (current)"
    )
    return parser.parse_args()


def commit_exists(sha: str) -> bool:
    """Check if a commit exists in the repository."""
    result = run_subprocess(["git", "cat-file", "-e", sha])
    return result.returncode == 0


def get_changed_files_diff(base: str, head: str) -> list[str]:
    """Get changed files using git diff."""
    result = run_subprocess(["git", "diff", "--name-only", base, head])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def get_changed_files_show(head: str) -> list[str]:
    """Get changed files using git show (fallback for single commit)."""
    result = run_subprocess(["git", "show", "--name-only", "--format=", head])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def get_changed_files(base: str, head: str) -> list[str]:
    """Get list of changed files between base and head commits.

    Handles edge cases:
    - Zero SHA (initial commit or force push): uses HEAD~1
    - Missing base commit (shallow clone): uses HEAD~1
    - Both fallback to git show if git diff fails
    """
    # Determine effective base commit
    if base == ZERO_SHA:
        # Initial commit or force push
        effective_base = "HEAD~1"
    elif commit_exists(base):
        effective_base = base
    else:
        # Shallow clone - base commit not available
        effective_base = "HEAD~1"

    # Try git diff first
    files = get_changed_files_diff(effective_base, head)
    if files:
        return files

    # Fallback to git show for current commit
    return get_changed_files_show(head)


def main() -> int:
    """Main entry point."""
    args = parse_args()
    files = get_changed_files(args.base, args.head)

    # Output in GitHub Actions format
    print(f"changed={chr(10).join(files)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
