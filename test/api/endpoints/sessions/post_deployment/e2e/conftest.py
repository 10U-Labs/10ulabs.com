from typing import Any, Dict

import pytest


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config: Dict[str, Any]) -> Dict[str, str]:
    return {
        "domain_name": shared_config["domain_name"],
        "api_fqdn": f"api.{shared_config['domain_name']}",
    }


@pytest.fixture(scope="module")
def api_url(config: Dict[str, Any]) -> str:
    return f"https://{config['api_fqdn']}"


@pytest.fixture(scope="module")
def test_device_id() -> str:
    return "e2e-test-device"


@pytest.fixture(scope="module")
def test_session_id() -> str:
    return "e2e-test-session-12345"
