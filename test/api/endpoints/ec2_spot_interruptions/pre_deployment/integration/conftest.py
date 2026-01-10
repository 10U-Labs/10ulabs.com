"""Shared fixtures for EC2 spot interruptions pre-deployment integration tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


EC2_SPOT_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ec2_spot_interruptions"
)


@pytest.fixture
def terraform_dir() -> Path:
    """Provide path to ec2_spot_interruptions terraform directory."""
    return EC2_SPOT_SRC_PATH
