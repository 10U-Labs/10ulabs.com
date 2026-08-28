from typing import Tuple

import pytest
import requests


def create_website_fixtures() -> Tuple:
    @pytest.fixture(name="website_url", scope="module")
    def _website_url_fixture(config):
        return f"https://{config['website_fqdn']}"

    @pytest.fixture(scope="module")
    def website_response(website_url):
        return requests.get(website_url, timeout=30)

    return _website_url_fixture, website_response
