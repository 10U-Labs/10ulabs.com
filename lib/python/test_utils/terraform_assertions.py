"""Terraform file existence assertion utilities."""
from pathlib import Path
from typing import List, Optional


def assert_terraform_files_exist(
    terraform_dir: Path,
    required_files: Optional[List[str]] = None,
) -> None:
    """Assert that required Terraform files exist in a directory.

    Args:
        terraform_dir: Path to the Terraform directory
        required_files: List of required file names. If None, uses default set.
    """
    if required_files is None:
        required_files = [
            "backend.tf",
            "providers.tf",
            "shared.tf",
            "locals.tf",
            "lambda.tf",
            "iam.tf",
            "sqs.tf",
            "eventbridge.tf",
            "outputs.tf",
        ]

    for filename in required_files:
        filepath = terraform_dir / filename
        assert filepath.exists(), f"Required file {filename} not found"


def assert_lambda_handler_exists(terraform_dir: Path) -> None:
    """Assert that the Lambda handler Python file exists.

    Args:
        terraform_dir: Path to the Terraform directory
    """
    handler_path = terraform_dir / "lambda" / "handler.py"
    assert handler_path.exists(), "Lambda handler.py not found"
