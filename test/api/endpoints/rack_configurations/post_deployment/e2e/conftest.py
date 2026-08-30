import pytest


@pytest.fixture(scope="module")
def api_url(config):
    return f"https://api.{config['domain_name']}"


@pytest.fixture(scope="module")
def website_url(config):
    return f"https://www.{config['domain_name']}"


@pytest.fixture(scope="module")
def test_device_id():
    return "e2e-test-device"
