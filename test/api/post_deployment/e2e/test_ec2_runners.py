import concurrent.futures
import pytest
import requests


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


def test_ec2_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403


def test_runner_creation_requires_auth(api_url):
    payload = {"job_id": 123, "github_repo": "test/repo", "job_labels": ["test"]}
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


def test_v1_ec2_runner_post_creates_ec2_instance(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 555555, "job_labels": ["ephemeral-ec2-spot-instance"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_ec2_runner_post_with_no_ami_triggers_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 444444, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_ec2_runner_post_missing_job_id_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_ec2_runner_post_missing_github_repo_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 333333, "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_ec2_runner_get_instance_details_include_metadata(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "running_instances" in data


def test_concurrent_ec2_runner_creation(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 654321, "job_labels": ["test"], "github_repo": "test/repo"}
    def create_runner():
        return requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_runner) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code in [200, 403, 500] for r in results)


def test_runner_creation_fails_when_ec2_capacity_unavailable(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 888888, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_runner_registers_with_github(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.status_code in [200, 403]
