from typing import Any, Dict

import pytest


@pytest.fixture(scope="module")
def api_url(config: Dict[str, Any]) -> str:
    return f"https://{config['api_fqdn']}"
