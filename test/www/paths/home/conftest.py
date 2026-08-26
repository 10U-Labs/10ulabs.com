from typing import Dict

import pytest

pytest_plugins = ['test_fixtures.website']


@pytest.fixture(scope="module")
def config(shared_config) -> Dict[str, str]:
    result = {}
    result['domain_name'] = shared_config.get('domain_name', '')
    result['website_fqdn'] = f"www.{shared_config.get('domain_name', '')}"
    return result
