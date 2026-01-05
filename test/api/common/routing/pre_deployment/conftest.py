"""Pytest configuration for pre-deployment tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


@pytest.fixture(name="openapi_path")
def openapi_path_fixture() -> Path:
    """Get the openapi.json path."""
    return REPO_ROOT / "src" / "www" / "api" / "openapi.json"


@pytest.fixture(name="apigateway_path")
def apigateway_path_fixture() -> Path:
    """Get the apigateway.tf path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "apigateway.tf"


@pytest.fixture(name="lambda_tf_path")
def lambda_tf_path_fixture() -> Path:
    """Get the lambda.tf path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda.tf"


@pytest.fixture(name="lambdas_dir")
def lambdas_dir_fixture() -> Path:
    """Get the lambdas directory path."""
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambdas"
