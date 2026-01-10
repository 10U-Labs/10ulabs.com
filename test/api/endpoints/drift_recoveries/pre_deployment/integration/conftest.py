"""Shared fixtures for drift recoveries pre-deployment integration tests."""
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture
def config(shared_config) -> Dict[str, str]:
    """Provide config for integration tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def terraform_dir() -> Path:
    """Provide the path to the Terraform directory."""
    return Path(__file__).parents[6] / 'src/api/endpoints/drift_recoveries'
