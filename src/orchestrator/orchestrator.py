#!/usr/bin/env python3
"""Orchestrator CLI for workflow management.

This is the main entry point for orchestrator commands. It provides subcommands
for computing root workflows, getting running workflows, canceling workflows,
and dispatching descendant workflows.

Usage:
    python3 src/orchestrator/orchestrator.py compute-roots <changed_files>
    python3 src/orchestrator/orchestrator.py get-running --repo owner/repo
    python3 src/orchestrator/orchestrator.py cancel --repo owner/repo --merge-roots '["x"]'
    python3 src/orchestrator/orchestrator.py dispatch --workflow bootstrap --repo owner/repo
"""
import sys


def main() -> int:
    """Main entry point that dispatches to subcommands."""
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command> [options]")
        print("\nCommands:")
        print("  compute-roots  Compute root workflows from changed files")
        print("  get-running    Get currently running workflows")
        print("  cancel         Cancel superseded workflow runs")
        print("  dispatch       Dispatch descendant workflows")
        return 1

    command = sys.argv[1]

    # Remove the command from argv so submodules see correct args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "compute-roots":
        import compute_roots
        compute_roots.main()
        return 0
    elif command == "get-running":
        import get_running
        return get_running.main()
    elif command == "cancel":
        import cancel
        return cancel.main()
    elif command == "dispatch":
        import dispatch
        return dispatch.main()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Available commands: compute-roots, get-running, cancel, dispatch")
        return 1


if __name__ == "__main__":
    sys.exit(main())
