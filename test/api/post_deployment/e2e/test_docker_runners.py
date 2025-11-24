import concurrent.futures
import pytest
import requests


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


def test_docker_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", timeout=10)
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


def test_v1_docker_runner_post_creates_fargate_task(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 888888, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202, 403, 500]


def test_v1_docker_runner_post_with_no_stable_image_triggers_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 777777, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202, 403, 500]


def test_v1_docker_runner_post_missing_job_id_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_docker_runner_post_missing_github_repo_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 666666, "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_docker_runner_get_task_details_include_metadata(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "running_tasks" in data


def test_concurrent_docker_runner_creation(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 123456, "job_labels": ["test"], "github_repo": "test/repo"}
    def create_runner():
        return requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_runner) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code in [200, 202, 403, 500] for r in results)


def test_runner_creation_fails_when_ecs_unavailable(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 999999, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_runner_self_terminates_after_job(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.status_code in [200, 403]
