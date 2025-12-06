"""Tests for API health and OpenAPI specification endpoints."""
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_root_endpoint_responds(api_url):
    """Verify root endpoint responds with 200 or redirect status code."""
    response = requests.get(api_url, headers=TEST_HEADERS, timeout=10)
    # 200 for direct response, 301/302 for redirect to docs
    assert response.status_code in [200, 301, 302]


def test_openapi_spec_accessible(api_url):
    """Verify OpenAPI specification is accessible."""
    response = requests.get(f"{api_url}/openapi.yml", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_yaml(api_url):
    """Verify OpenAPI specification has correct YAML content type."""
    response = requests.get(f"{api_url}/openapi.yml", headers=TEST_HEADERS, timeout=10)
    content_type = response.headers.get("Content-Type", "")
    is_yaml = "application/x-yaml" in content_type or "text/yaml" in content_type
    assert is_yaml
