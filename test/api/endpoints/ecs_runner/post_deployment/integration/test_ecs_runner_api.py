import requests

from ..conftest import make_authenticated_get, make_authenticated_post


def test_ecs_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/ecs-runner", timeout=10)
    assert response.status_code == 403


def test_ecs_runner_status_accepts_valid_api_key(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert response.status_code == 200


def test_ecs_runner_status_returns_json(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_ecs_runner_status_has_success_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "success" in response.json()


def test_ecs_runner_status_has_running_tasks_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "running_tasks" in response.json()


def test_ecs_runner_status_has_tasks_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "tasks" in response.json()


def test_ecs_runner_status_has_cluster_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "cluster" in response.json()


def test_v1_ecs_runner_post_missing_job_id_returns_400(api_url, api_key):
    payload = {
        "job_labels": ["ephemeral-ecs-fargate"],
        "github_repo": "any/repo"
    }
    response = make_authenticated_post(
        f"{api_url}/v1/ecs-runner", api_key, json=payload
    )
    assert response.status_code == 400


def test_v1_ecs_runner_post_missing_github_repo_returns_400(api_url, api_key):
    payload = {
        "job_id": 666666,
        "job_labels": ["ephemeral-ecs-fargate"]
    }
    response = make_authenticated_post(
        f"{api_url}/v1/ecs-runner", api_key, json=payload
    )
    assert response.status_code == 400
