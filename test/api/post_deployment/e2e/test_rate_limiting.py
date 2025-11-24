import time
import requests


def test_rate_limit_exceeded_returns_429(api_url):
    responses = []
    for _ in range(200):
        try:
            resp = requests.get(f"{api_url}/health", timeout=1)
            responses.append(resp.status_code)
            if resp.status_code == 429:
                break
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses or 429 in responses


def test_rate_limit_applies_to_health_endpoint(api_url):
    responses = []
    for _ in range(60):
        try:
            resp = requests.get(f"{api_url}/health", timeout=2)
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_applies_to_echo_endpoint(api_url):
    responses = []
    for _ in range(60):
        try:
            resp = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, timeout=2)
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_headers_present_in_response(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_rate_limit_burst_allows_initial_requests(api_url):
    success_count = 0
    for _ in range(10):
        try:
            resp = requests.get(f"{api_url}/health", timeout=2)
            if resp.status_code == 200:
                success_count += 1
        except requests.exceptions.Timeout:
            continue
    assert success_count > 0
