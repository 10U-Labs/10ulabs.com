import pytest
import requests


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture():
    return "https://10ulabs.com"


@pytest.fixture(name="website_response", scope="module")
def website_response_fixture(website_url):
    return requests.get(website_url, timeout=30)
