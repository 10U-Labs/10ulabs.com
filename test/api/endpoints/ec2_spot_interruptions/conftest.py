"""Shared fixtures for EC2 spot interruptions tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


EC2_SPOT_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ec2_spot_interruptions"
)
EC2_SPOT_LAMBDA_PATH = EC2_SPOT_SRC_PATH / "lambda"


@pytest.fixture
def ec2_spot_src_path() -> Path:
    """Provide path to ec2_spot_interruptions source directory."""
    return EC2_SPOT_SRC_PATH


@pytest.fixture
def ec2_spot_lambda_path() -> Path:
    """Provide path to ec2_spot_interruptions lambda directory."""
    return EC2_SPOT_LAMBDA_PATH
