import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    return config["aws_region"]


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    return f"https://{config['api_fqdn']}"
