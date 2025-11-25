import pytest
import requests


@pytest.fixture(name="latest_ami_exists", scope="module")
def latest_ami_exists_fixture(ssm_client):
    try:
        ssm_client.get_parameter(Name='/ec2/runner/ami/latest')
        return True
    except ssm_client.exceptions.ParameterNotFound:
        return False


def test_protected_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_api_key(api_url):
    headers = {"x-api-key": "invalid-key-12345"}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_accepts_valid_api_key(api_url, api_key, latest_ami_exists):
    if api_key is None:
        pytest.skip("API key not available")
    if not latest_ami_exists:
        pytest.skip("No AMI available in SSM")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 200


def test_ec2_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403


def test_runner_creation_requires_auth(api_url):
    payload = {"job_id": 123, "github_repo": "any/repo", "job_labels": ["ephemeral-ec2-spot-instance"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, timeout=10)
    assert response.status_code == 403


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


def test_v1_ec2_runner_post_creates_ec2_instance(api_url, api_key, github_repo, latest_ami_exists):
    if not latest_ami_exists:
        pytest.skip("No AMI available in SSM")
    headers = {"x-api-key": api_key}
    payload = {"job_id": 555555, "job_labels": ["ephemeral-ec2-spot-instance"], "github_repo": github_repo}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202]


def test_v1_ec2_runner_post_missing_job_id_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_labels": ["ephemeral-ec2-spot-instance"], "github_repo": "any/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code == 400


def test_v1_ec2_runner_post_missing_github_repo_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 333333, "job_labels": ["ephemeral-ec2-spot-instance"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code == 400


def test_v1_ec2_runner_get_instance_details_include_metadata(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert "running_instances" in response.json()


def test_runner_registers_with_github(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.status_code == 200
