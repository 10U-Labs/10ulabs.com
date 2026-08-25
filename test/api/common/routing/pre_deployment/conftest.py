"""Pytest configuration for pre-deployment tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


@pytest.fixture
def openapi_path() -> Path:
    """Get the openapi.json path."""
    return REPO_ROOT / "src" / "www" / "api" / "openapi.json"


@pytest.fixture
def apigateway_path() -> Path:
    """Get the apigateway.tf path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "apigateway.tf"


@pytest.fixture
def lambda_tf_path() -> Path:
    """Get the lambda.tf path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda.tf"


@pytest.fixture
def lambda_dir() -> Path:
    """Get the lambda directory path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda"
