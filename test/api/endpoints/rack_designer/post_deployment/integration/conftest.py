import pytest


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    return f"https://www.{config['domain_name']}"
