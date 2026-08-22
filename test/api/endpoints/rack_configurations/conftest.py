"""Pytest configuration and fixtures for rack designer tests."""
from typing import Dict

import pytest

from test_fixtures.integration import get_aws_account_id_via_cli


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide rack designer configuration for tests."""
    result = {
        'aws_region': shared_config['aws_region'],
        'aws_account_id': get_aws_account_id_via_cli(),
        'domain_name': shared_config['domain_name'],
        'api_fqdn': f"api.{shared_config['domain_name']}",
        'resource_prefix': shared_config['resource_prefix']
    }
    return result
