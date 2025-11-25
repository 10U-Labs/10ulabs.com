from test.api.post_deployment.conftest import make_authenticated_get, make_authenticated_post
import pytest
import requests


def test_docker_runner_endpoint_requires_auth(api_url):
    url = f"{api_url}/v1/image-for-docker-runners/latest"
    response = requests.get(url, timeout=10)
    assert response.status_code == 403


def test_docker_runner_endpoint_accepts_valid_api_key(api_url, api_key):
    if api_key is None:
        pytest.skip("API key not available")
    response = make_authenticated_get(
        f"{api_url}/v1/image-for-docker-runners/latest", api_key
    )
    assert response.status_code != 403


def test_docker_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/docker-runner", timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_accepts_valid_api_key(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert response.status_code == 200


def test_docker_runner_status_returns_json(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_docker_runner_status_has_success_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert "success" in response.json()


def test_docker_runner_status_has_running_tasks_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert "running_tasks" in response.json()


def test_docker_runner_status_has_tasks_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert "tasks" in response.json()


def test_docker_runner_status_has_cluster_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    assert "cluster" in response.json()


def test_v1_docker_runner_post_missing_job_id_returns_400(api_url, api_key):
    payload = {
        "job_labels": ["ephemeral-ecs-fargate-spot"],
        "github_repo": "any/repo"
    }
    response = make_authenticated_post(
        f"{api_url}/v1/docker-runner", api_key, json=payload
    )
    assert response.status_code == 400


def test_v1_docker_runner_post_missing_github_repo_returns_400(api_url, api_key):
    payload = {
        "job_id": 666666,
        "job_labels": ["ephemeral-ecs-fargate-spot"]
    }
    response = make_authenticated_post(
        f"{api_url}/v1/docker-runner", api_key, json=payload
    )
    assert response.status_code == 400
