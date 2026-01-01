"""Pytest fixtures for pre-deployment integration tests."""
import json

import pytest

from repo_utils import REPO_ROOT

RUNNERS_CONFIG_PATH = REPO_ROOT / "etc" / "runners.json"


@pytest.fixture(scope="session")
def runners_config():
    """Load runners configuration from etc/runners.json."""
    with open(RUNNERS_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def ami_purpose_value(runners_config):
    """Get the AMI purpose tag value from runners config."""
    return runners_config["tags"]["ec2"]["ami"]["purpose_value"]


@pytest.fixture(scope="session")
def ami_stable_tag(runners_config):
    """Get the AMI stable tag name from runners config."""
    return runners_config["tags"]["ec2"]["ami"]["stable_tag"]
