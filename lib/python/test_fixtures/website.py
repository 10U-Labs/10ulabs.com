from typing import Dict, Tuple

import pytest
import requests


def create_website_fixtures() -> Tuple:
    @pytest.fixture(name="website_url", scope="module")
    def _website_url_fixture(config: Dict[str, str]) -> str:
        return f"https://{config['website_fqdn']}"

    @pytest.fixture(scope="module")
    def website_response(website_url: str) -> requests.Response:
        return requests.get(website_url, timeout=30)

    return _website_url_fixture, website_response
