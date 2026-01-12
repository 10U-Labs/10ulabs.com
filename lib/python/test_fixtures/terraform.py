"""Terraform utilities for pytest tests.

Provides functions to run terraform init and output commands,
useful for integration tests that need to read terraform state.

Use by adding to conftest.py:
    from test_fixtures.terraform import terraform_init, terraform_output
"""
import subprocess
from pathlib import Path
from typing import Callable

import pytest


def create_tf_content_fixture(filename: str) -> Callable:
    """Create a pytest fixture that reads a terraform file's content.

    Usage in conftest.py:
        from test_fixtures.terraform import create_tf_content_fixture
        fixture_lambda_tf = create_tf_content_fixture("lambda.tf")

    Args:
        filename: Name of the .tf file to read

    Returns:
        A pytest fixture function that reads the file content
    """
    fixture_name = filename.replace(".", "_") + "_content"

    @pytest.fixture(name=fixture_name)
    def fixture_func(terraform_dir: Path) -> str:
        """Provide terraform file content."""
        return (terraform_dir / filename).read_text()

    return fixture_func


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
    result = subprocess.run(
        ["terraform", "output", "-raw", name],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def terraform_output_json(directory: Path, name: str) -> str:
    """Get a terraform output value as JSON string.

    Args:
        directory: Path to the terraform directory
        name: Name of the output variable

    Returns:
        The output value as a JSON string, or empty string if not found
    """
    result = subprocess.run(
        ["terraform", "output", "-json", name],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""
