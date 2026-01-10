"""Shared fixtures for EC2 spot interruptions pre-deployment tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


EC2_SPOT_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ec2_spot_interruptions"
)


@pytest.fixture
def ec2_spot_src_path() -> Path:
    """Provide path to ec2_spot_interruptions source directory."""
    return EC2_SPOT_SRC_PATH


@pytest.fixture
def terraform_dir() -> Path:
    """Provide path to ec2_spot_interruptions terraform directory."""
    return EC2_SPOT_SRC_PATH
