"""Tests to validate endpoint_health infrastructure exists before api_shared_ecr deployment."""
import requests


def test_health_endpoint_responds(endpoint_health_outputs):
    """Verify the health endpoint is accessible."""
    health_url = endpoint_health_outputs.get("health_endpoint_url")
    assert health_url, "health_endpoint_url output not found in endpoint_health"
    response = requests.get(health_url, timeout=10)
    assert response.status_code == 200
