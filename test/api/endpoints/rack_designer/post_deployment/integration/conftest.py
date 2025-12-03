import pytest


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    return f"https://www.{config['domain_name']}"


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    return "integration-test-device"
