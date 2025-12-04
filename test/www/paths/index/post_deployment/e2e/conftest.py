import pytest
import requests


@pytest.fixture(name="nonexistent_page_response", scope="module")
def nonexistent_page_response_fixture(website_url):
    return requests.get(f"{website_url}/nonexistent-page-12345", timeout=30)


@pytest.fixture(name="privacy_page_response", scope="module")
def privacy_page_response_fixture(website_url):
    return requests.get(f"{website_url}/privacy.html", timeout=30)
