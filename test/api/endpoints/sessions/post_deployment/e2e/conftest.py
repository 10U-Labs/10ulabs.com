import pytest


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config):
    return {
        "domain_name": shared_config["domain_name"],
        "api_fqdn": f"api.{shared_config['domain_name']}",
    }


@pytest.fixture(scope="module")
def api_url(config):
    return f"https://{config['api_fqdn']}"


@pytest.fixture(scope="module")
def test_device_id():
    return "e2e-test-device"


@pytest.fixture(scope="module")
def test_session_id():
    return "e2e-test-session-12345"
