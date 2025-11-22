import os
import re
import requests
import pytest
import boto3


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


@pytest.fixture(scope="module")
def api_key(tfvars):
    ssm_client = boto3.client('ssm', region_name=tfvars.get('aws_region', 'us-east-1'))
    try:
        response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
        return response['Parameter']['Value']
    except Exception:
        return None


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


def test_echo_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_returns_echoed_data(api_url):
    test_data = {"message": "hello", "number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    data = response.json()
    assert data["echo"] == test_data


def test_protected_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_api_key(api_url):
    headers = {"x-api-key": "invalid-key-12345"}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_accepts_valid_api_key(api_url, api_key):
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", timeout=10)
    assert response.status_code == 403


def test_docker_runner_endpoint_accepts_valid_api_key(api_url, api_key):
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code != 403


def test_docker_runner_endpoint_returns_images_when_available(api_url, api_key, ecr_image_count):
    if ecr_image_count == 0:
        pytest.skip("No ECR images available")
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_endpoint_returns_error_when_no_images(api_url, api_key, ecr_image_count):
    if ecr_image_count > 0:
        pytest.skip("ECR images exist")
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [404, 500]


def test_ec2_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403


def test_docker_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", timeout=10)
    assert response.status_code == 403


def test_runner_creation_requires_auth(api_url):
    payload = {"job_id": 123, "github_repo": "test/repo", "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/docker-runner", timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_accepts_valid_api_key(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_status_returns_json(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_docker_runner_status_has_success_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "success" in data


def test_docker_runner_status_has_running_tasks_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "running_tasks" in data


def test_docker_runner_status_has_tasks_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "tasks" in data


def test_docker_runner_status_has_cluster_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "cluster" in data


def test_ec2_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/ec2-runner", timeout=10)
    assert response.status_code == 403


def test_ec2_runner_status_accepts_valid_api_key(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.status_code == 200


def test_ec2_runner_status_returns_json(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_ec2_runner_status_has_success_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "success" in data


def test_ec2_runner_status_has_running_instances_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "running_instances" in data


def test_ec2_runner_status_has_instances_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "instances" in data


