"""Terraform utilities for pytest tests.

Provides functions to run terraform init and output commands,
useful for integration tests that need to read terraform state.

Use by adding to conftest.py:
    from test_fixtures.terraform import terraform_init, terraform_output
"""
import subprocess
from pathlib import Path


def terraform_init(directory: Path) -> bool:
    """Initialize terraform in the given directory.

    Args:
        directory: Path to the terraform directory

    Returns:
        True if terraform init succeeded, False otherwise
    """
    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def terraform_output(directory: Path, name: str) -> str:
    """Get a terraform output value.

    Args:
        directory: Path to the terraform directory
        name: Name of the output variable

    Returns:
        The output value as a string, or empty string if not found
    """
    cmd = ["terraform", "output", "-raw", name]
    result = subprocess.run(
        cmd,
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""
