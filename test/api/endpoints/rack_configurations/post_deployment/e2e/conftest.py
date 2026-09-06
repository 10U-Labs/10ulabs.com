from typing import Any, Dict

import pytest


@pytest.fixture(scope="module")
def api_url(config: Dict[str, Any]) -> str:
    return f"https://api.{config['domain_name']}"


@pytest.fixture(scope="module")
def test_device_id() -> str:
    return "e2e-test-device"
