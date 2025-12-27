#!/usr/bin/env python3
"""Workflowctl CLI for workflow management.

This is the main entry point for workflowctl commands. It provides subcommands
for computing root workflows, getting running workflows, canceling workflows,
and dispatching descendant workflows.

Usage:
    python3 src/workflowctl/workflowctl.py compute-root-workflows <changed_files>
    python3 src/workflowctl/workflowctl.py get-running-workflows --repo owner/repo
    python3 src/workflowctl/workflowctl.py cancel-workflows --repo owner/repo --merge-roots '["x"]'
    python3 src/workflowctl/workflowctl.py dispatch-descendant-workflows --workflow bootstrap --repo owner/repo
    python3 src/workflowctl/workflowctl.py get-changed-files --base SHA --head SHA
    python3 src/workflowctl/workflowctl.py dispatch-root-workflows --repo owner/repo --roots ROOTS
"""
import sys

import cancel
import compute_roots
import dispatch_descendants
import dispatch_roots
import get_changed_files
import get_running


COMMANDS = {
    "cancel-workflows": ("Cancel superseded workflow runs", cancel.main),
    "compute-root-workflows": ("Compute root workflows from changed files", compute_roots.main),
    "dispatch-descendant-workflows": ("Dispatch descendant workflows", dispatch_descendants.main),
    "dispatch-root-workflows": ("Dispatch root workflows", dispatch_roots.main),
    "get-changed-files": ("Get changed files between commits", get_changed_files.main),
    "get-running-workflows": ("Get currently running workflows", get_running.main),
}


def main() -> int:
    """Main entry point that dispatches to subcommands."""
    if len(sys.argv) < 2:
        print("Usage: workflowctl.py <command> [options]")
        print("\nCommands:")
        for cmd, (desc, _) in COMMANDS.items():
            print(f"  {cmd:30} {desc}")
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
