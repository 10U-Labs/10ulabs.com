from typing import Any, Dict

import pytest


@pytest.fixture(scope="module")
def config(shared_config: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    result['aws_region'] = shared_config['aws_region']
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    result['domain_name'] = shared_config.get('domain_name', '')
    return result
