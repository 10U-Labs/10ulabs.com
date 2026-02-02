"""Terraform file existence check utilities."""
from pathlib import Path
from typing import List, Optional


# Default Terraform files required by endpoint modules
DEFAULT_TERRAFORM_FILES = [
    "backend.tf",
    "providers.tf",
    "shared.tf",
    "locals.tf",
    "lambda.tf",
    "iam.tf",
    "outputs.tf",
]


def get_missing_terraform_files(
    terraform_dir: Path,
    required_files: Optional[List[str]] = None,
) -> List[str]:
    """Check for missing Terraform files in a directory.

    Args:
        terraform_dir: Path to the Terraform directory
        required_files: List of required file names. If None, uses default set.

    Returns:
        List of missing filenames (empty if all exist).
    """
    files_to_check = required_files if required_files is not None else DEFAULT_TERRAFORM_FILES
    return [f for f in files_to_check if not (terraform_dir / f).exists()]


def lambda_handler_exists(terraform_dir: Path) -> bool:
    """Check if the Lambda handler Python file exists.

    Args:
        terraform_dir: Path to the Terraform directory

    Returns:
        True if handler.py exists, False otherwise.
    """
    return (terraform_dir / "lambda" / "handler.py").exists()
