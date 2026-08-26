from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


@pytest.fixture
def openapi_path() -> Path:
    return REPO_ROOT / "src" / "www" / "api" / "openapi.json"


@pytest.fixture
def apigateway_path() -> Path:
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "apigateway.tf"


@pytest.fixture
def lambda_tf_path() -> Path:
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda.tf"


@pytest.fixture
def lambda_dir() -> Path:
    return REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda"
