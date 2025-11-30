import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_root_endpoint_responds(api_url):
    response = requests.get(api_url, headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_accessible(api_url):
    response = requests.get(f"{api_url}/openapi.yml", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_yaml(api_url):
    response = requests.get(f"{api_url}/openapi.yml", headers=TEST_HEADERS, timeout=10)
    assert "application/x-yaml" in response.headers.get("Content-Type", "") or "text/yaml" in response.headers.get("Content-Type", "")
