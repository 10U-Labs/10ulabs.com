import requests


def test_cloudfront_delivers_404_page_for_nonexistent_endpoint(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "404" in response.text


def test_cloudfront_404_page_contains_not_found_text(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "Not Found" in response.text or "Endpoint not found" in response.text


def test_cloudfront_404_page_has_link_to_docs(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "API Documentation" in response.text or "/" in response.text
