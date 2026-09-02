from typing import Any, Dict, Optional

import pytest


@pytest.fixture(scope="module")
def api_url(config: Dict[str, Any]) -> str:
    return f"https://{config['api_fqdn']}"


@pytest.fixture(scope="module")
def api_key(ssm_client: Any) -> Optional[str]:
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None
