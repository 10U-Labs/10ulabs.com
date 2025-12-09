"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"


def _terraform_init(directory: Path) -> bool:
    """Initialize terraform in the given directory."""
    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def _terraform_output(directory: Path, name: str) -> str:
    """Get a terraform output value."""
    cmd = ["terraform", "output", "-raw", name]
    result = subprocess.run(
        cmd,
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_shared_ecr state access."""
    return _terraform_init(API_SHARED_ECR_DIR)


@pytest.fixture(scope="session")
def api_shared_ecr_outputs(request):
    """Get api_shared_ecr terraform outputs."""
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_ecr")
    return {
        "repository_name": _terraform_output(API_SHARED_ECR_DIR, "ecr_repository_name"),
        "repository_url": _terraform_output(API_SHARED_ECR_DIR, "ecr_repository_url"),
        "repository_arn": _terraform_output(API_SHARED_ECR_DIR, "ecr_repository_arn"),
    }
