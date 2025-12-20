#!/usr/bin/env python3
"""Determine if static analysis or unit tests should run.

This module checks if any changed files match the patterns that require
running static analysis or unit tests for the workflowctl.

Usage:
    python3 src/workflowctl/workflowctl.py should-run \
        --check static-analysis --changed "file1.py\\nfile2.py"
"""
import argparse
import sys

from utils import file_matches_pattern


# Files that trigger static analysis
STATIC_ANALYSIS_PATTERNS = [
    ".github/workflows/workflowctl.yml",
    "etc/workflow-dependencies.json",
    "src/workflowctl/*.py",
]

# Files that trigger unit tests
UNIT_TEST_PATTERNS = [
    ".github/workflows/workflowctl.yml",
    "src/workflowctl/*.py",
    "test/workflowctl/**",
]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Check if static analysis or unit tests should run"
    )
    parser.add_argument(
        "--check",
        required=True,
        choices=["static-analysis", "unit-tests"],
        help="Which check to perform"
    )
    parser.add_argument(
        "--changed",
        required=True,
        help="Newline-separated list of changed files"
    )
    return parser.parse_args()


def should_run(changed_files: list[str], patterns: list[str]) -> bool:
    """Check if any changed file matches any pattern."""
    for filepath in changed_files:
        for pattern in patterns:
            if file_matches_pattern(filepath, pattern):
                return True
    return False


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse changed files
    changed_files = [
        f.strip() for f in args.changed.split("\n") if f.strip()
    ]

    # Get patterns for the check type
    if args.check == "static-analysis":
        patterns = STATIC_ANALYSIS_PATTERNS
    else:
        patterns = UNIT_TEST_PATTERNS

    # Check if should run
    result = should_run(changed_files, patterns)

    # Output in GitHub Actions format
    print(f"should_run={'true' if result else 'false'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
