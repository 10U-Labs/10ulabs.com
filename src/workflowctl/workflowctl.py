#!/usr/bin/env python3
"""Workflowctl CLI for workflow management.

This is the main entry point for workflowctl commands. It provides subcommands
for computing root workflows, getting running workflows, canceling workflows,
and dispatching descendant workflows.

Usage:
    python3 src/workflowctl/workflowctl.py compute-roots <changed_files>
    python3 src/workflowctl/workflowctl.py get-running --repo owner/repo
    python3 src/workflowctl/workflowctl.py cancel --repo owner/repo --merge-roots '["x"]'
    python3 src/workflowctl/workflowctl.py dispatch --workflow bootstrap --repo owner/repo
    python3 src/workflowctl/workflowctl.py get-changed-files --base SHA --head SHA
    python3 src/workflowctl/workflowctl.py should-run --check static-analysis --changed FILES
    python3 src/workflowctl/workflowctl.py dispatch-roots --repo owner/repo --roots ROOTS
"""
import sys

import cancel
import compute_roots
import dispatch
import dispatch_roots
import get_changed_files
import get_running
import should_run


COMMANDS = {
    "compute-roots": ("Compute root workflows from changed files", compute_roots.main),
    "get-running": ("Get currently running workflows", get_running.main),
    "cancel": ("Cancel superseded workflow runs", cancel.main),
    "dispatch": ("Dispatch descendant workflows", dispatch.main),
    "get-changed-files": ("Get changed files between commits", get_changed_files.main),
    "should-run": ("Check if static analysis/tests should run", should_run.main),
    "dispatch-roots": ("Dispatch root workflows", dispatch_roots.main),
}


def main() -> int:
    """Main entry point that dispatches to subcommands."""
    if len(sys.argv) < 2:
        print("Usage: workflowctl.py <command> [options]")
        print("\nCommands:")
        for cmd, (desc, _) in COMMANDS.items():
            print(f"  {cmd:20} {desc}")
        return 1

    command = sys.argv[1]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        return 1

    # Remove the command from argv so submodules see correct args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    _, handler = COMMANDS[command]
    result = handler()
    return result if result is not None else 0


if __name__ == "__main__":
    sys.exit(main())
