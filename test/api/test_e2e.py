import os
import re
import requests
import pytest


@pytest.fixture(scope="module")
def tfvars():
    tfvars_path = os.path.join(os.path.dirname(__file__), "../../src/api/terraform.tfvars")
    config = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip('"')
    return config


@pytest.fixture(scope="module")
def api_url(tfvars):
    return f"https://{tfvars['domain_subdomain']}"


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


def test_invalid_endpoint_returns_404(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_openapi_spec_accessible(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_yaml(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert "application/x-yaml" in response.headers.get("Content-Type", "") or "text/yaml" in response.headers.get("Content-Type", "")
