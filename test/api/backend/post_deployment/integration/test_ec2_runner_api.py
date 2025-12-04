"""Tests for EC2 runner API authentication and authorization."""
import requests


def test_protected_endpoint_requires_auth(api_url):
    """Verify protected endpoint returns 403 without auth."""
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_api_key(api_url):
    """Verify protected endpoint rejects invalid API key."""
    headers = {"x-api-key": "invalid-key-12345"}
    url = f"{api_url}/v1/image-for-ec2-runners/latest"
    response = requests.get(url, headers=headers, timeout=10)
    assert response.status_code == 403


def test_ec2_runner_list_requires_auth(api_url):
    """Verify EC2 runner list endpoint requires authentication."""
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403
