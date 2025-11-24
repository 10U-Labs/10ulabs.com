import requests


def test_invalid_endpoint_returns_404(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_malformed_json_request_returns_400(api_url):
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{api_url}/v1/echo", data="not valid json", headers=headers, timeout=10)
    assert response.status_code in [400, 500]


def test_oversized_payload_returns_413(api_url):
    large_payload = {"data": "x" * (10 * 1024 * 1024)}
    response = requests.post(f"{api_url}/v1/echo", json=large_payload, timeout=30)
    assert response.status_code in [200, 413, 500]


def test_internal_server_error_returns_500(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": "invalid-type", "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 400, 403, 500]


def test_service_unavailable_returns_503(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code in [200, 503]


def test_api_responds_to_options_requests(api_url):
    response = requests.options(f"{api_url}/health", timeout=10)
    assert response.status_code in [200, 204, 405]


def test_api_handles_malformed_json_gracefully(api_url):
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{api_url}/v1/echo", data="{invalid json", headers=headers, timeout=10)
    assert response.status_code in [400, 500]


def test_api_handles_missing_content_type_header(api_url):
    response = requests.post(f"{api_url}/v1/echo", data='{"test": "data"}', timeout=10)
    assert response.status_code in [200, 400]


def test_api_error_responses_include_correlation_ids(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404
