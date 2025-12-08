"""Pytest configuration and fixtures for rack designer tests."""
from typing import Dict

import pytest


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide rack designer configuration for tests."""
    result = {
        'aws_region': shared_config.get('aws_region', ''),
        'aws_account_id': shared_config.get('aws_account_id', ''),
        'domain_name': shared_config.get('domain_name', ''),
        'api_fqdn': f"api.{shared_config.get('domain_name', '')}",
        'resource_prefix': shared_config.get('resource_prefix', '')
    }
    return result
