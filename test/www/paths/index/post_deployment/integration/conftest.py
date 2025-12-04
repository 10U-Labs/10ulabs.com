import pytest
import requests


@pytest.fixture(name="home_page_response", scope="module")
def home_page_response_fixture(website_url):
    return requests.get(website_url, timeout=30)


@pytest.fixture(name="contact_section_response", scope="module")
def contact_section_response_fixture(website_url):
    return requests.get(f"{website_url}/#contact", timeout=30)


@pytest.fixture(name="products_section_response", scope="module")
def products_section_response_fixture(website_url):
    return requests.get(f"{website_url}/#products", timeout=30)


@pytest.fixture(name="privacy_page_response", scope="module")
def privacy_page_response_fixture(website_url):
    return requests.get(f"{website_url}/privacy.html", timeout=30)
