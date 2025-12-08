"""Pytest configuration and fixtures for rack designer tests."""
from typing import Dict

from test.api.conftest import parse_shared_module_outputs

import pytest


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    """Provide rack designer configuration for tests."""
    shared = parse_shared_module_outputs()
    result = {
        'aws_region': shared.get('aws_region', ''),
        'aws_account_id': shared.get('aws_account_id', ''),
        'domain_name': shared.get('domain_name', ''),
        'api_fqdn': f"api.{shared.get('domain_name', '')}",
        'resource_prefix': shared.get('resource_prefix', '')
    }
    return result
