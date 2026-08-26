import pytest


@pytest.fixture(scope="module")
def api_url(config):
    return f"https://{config['api_fqdn']}"
