import pytest


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    return f"https://{config['website_fqdn']}"
