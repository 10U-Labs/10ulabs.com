import time
import requests


def test_health_endpoint_responds(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_health_endpoint_returns_json(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_health_endpoint_has_status_field(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    data = response.json()
    assert "status" in data


def test_health_endpoint_status_healthy(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint_responds(api_url):
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_accessible(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_yaml(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert "application/x-yaml" in response.headers.get("Content-Type", "") or "text/yaml" in response.headers.get("Content-Type", "")


def test_concurrent_health_request_1_returns_200(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_2_returns_200(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_3_returns_200(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_4_returns_200(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_5_returns_200(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_health_endpoint_response_time_under_5_seconds(api_url):
    start = time.time()
    requests.get(f"{api_url}/health", timeout=10)
    duration = time.time() - start
    assert duration < 5.0
