"""Mock utilities for workflowctl tests.

This module provides factory functions for creating mock objects commonly
used in workflowctl tests, particularly for subprocess.run results.

Usage:
    from workflowctl_mocks import create_subprocess_result

    mock_result = create_subprocess_result(returncode=0, stdout="success")
    with patch("module.subprocess.run", return_value=mock_result):
        ...
"""

from typing import Optional
from unittest.mock import MagicMock


def create_subprocess_result(
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> MagicMock:
    """Create a mock subprocess.CompletedProcess result.

    Args:
        returncode: The return code of the subprocess. Default 0 (success).
        stdout: The stdout output. Default empty string.
        stderr: The stderr output. Default empty string.

    Returns:
        A MagicMock configured to behave like subprocess.CompletedProcess.

    Example:
        >>> result = create_subprocess_result(returncode=0, stdout="12345\\n")
        >>> result.returncode
        0
        >>> result.stdout
        '12345\\n'
    """
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def create_gh_workflow_list_result(
    workflow_names: Optional[list[str]] = None,
) -> MagicMock:
    """Create a mock result for 'gh run list' command.

    Args:
        workflow_names: List of workflow names to include in output.
            If None, returns empty output (no running workflows).

    Returns:
        A MagicMock with stdout containing tab-separated workflow data.

    Example:
        >>> result = create_gh_workflow_list_result(["Bootstrap", "WWW Shared"])
        >>> "Bootstrap" in result.stdout
        True
    """
    if workflow_names is None:
        workflow_names = []

    lines = []
    for i, name in enumerate(workflow_names):
        # Format: status\tconclusion\tworkflow_name\tbranch\tevent\trun_id
        lines.append(f"in_progress\t\t{name}\tmain\tpush\t{100000 + i}")

    stdout = "\n".join(lines)
    return create_subprocess_result(returncode=0, stdout=stdout)
