"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
API_BACKEND_DIR = REPO_ROOT / "src" / "api" / "backend"


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
def apigateway_client(aws_region):
    """Create an API Gateway client."""
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_backend state access."""
    return _terraform_init(API_BACKEND_DIR)


@pytest.fixture(scope="session")
def api_backend_outputs(request):
    """Get api_backend terraform outputs."""
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for api_backend")
    return {
        "api_gateway_rest_api_id": _terraform_output(
            API_BACKEND_DIR, "api_gateway_rest_api_id"
        ),
    }
