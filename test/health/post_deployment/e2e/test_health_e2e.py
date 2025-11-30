import time
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_health_endpoint_stable_over_sequential_requests(api_url):
    responses = [requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10) for _ in range(5)]
    statuses = [r.status_code for r in responses]
    assert all(s == 200 for s in statuses)


def test_health_endpoint_consistent_response_body(api_url):
    responses = [requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10) for _ in range(3)]
    bodies = [r.json() for r in responses]
    assert all(b["status"] == "healthy" for b in bodies)


def test_health_endpoint_average_response_time_acceptable(api_url):
    times = []
    for _ in range(5):
        start = time.time()
        requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
        times.append(time.time() - start)
    avg_time = sum(times) / len(times)
    assert avg_time < 2.0


def test_health_endpoint_no_cold_start_degradation(api_url):
    first_response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    time.sleep(1)
    second_response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert first_response.status_code == second_response.status_code


def test_health_endpoint_returns_valid_json_structure(api_url):
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    body = response.json()
    required_fields = ["status", "service", "version"]
    assert all(field in body for field in required_fields)


def test_health_endpoint_service_field_matches_expected(api_url):
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    body = response.json()
    assert body["service"] == "10U Labs API"


def test_health_endpoint_version_field_format_valid(api_url):
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    body = response.json()
    version_parts = body["version"].split(".")
    assert len(version_parts) == 3
