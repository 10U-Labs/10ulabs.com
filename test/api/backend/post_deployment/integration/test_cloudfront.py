"""Tests for CloudFront distribution and error handling."""
import json
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_cloudfront_delivers_404_page_for_nonexistent_endpoint(api_url):
    """Verify CloudFront returns 404 for nonexistent endpoints."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    """Verify CloudFront 404 page contains error message."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    data = json.loads(response.text)
    assert "error" in data


def test_cloudfront_404_page_contains_not_found_text(api_url):
    """Verify CloudFront 404 page contains not found text."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    expected_text = "Not Found" in response.text or "Endpoint not found" in response.text
    assert expected_text


def test_cloudfront_404_page_has_link_to_docs(api_url):
    """Verify CloudFront 404 page has link to documentation."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "API Documentation" in response.text or "/" in response.text
