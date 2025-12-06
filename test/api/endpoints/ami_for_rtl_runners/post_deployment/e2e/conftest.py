"""E2E test fixtures for RTL runner images."""

import os

import pytest


@pytest.fixture
def github_pat() -> str:
    """Return GitHub PAT for runner registration."""
    pat = os.environ.get("GITHUB_PAT")
    if not pat:
        pytest.skip("GITHUB_PAT environment variable not set")
    return pat


@pytest.fixture
def github_repo() -> str:
    """Return GitHub repository for runner registration."""
    return "10U-Labs-LLC/10ulabs.com"
