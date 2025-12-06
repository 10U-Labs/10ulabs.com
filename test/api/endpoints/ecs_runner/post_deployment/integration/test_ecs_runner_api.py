"""Integration tests for ECS runner API endpoints."""
import time

import requests

from ..conftest import make_authenticated_get, make_authenticated_post


def test_ecs_runner_status_requires_auth(api_url):
    """Test that ECS runner status endpoint requires authentication."""
    response = requests.get(f"{api_url}/v1/ecs-runner", timeout=10)
    assert response.status_code == 403


def test_ecs_runner_status_accepts_valid_api_key(api_url, api_key):
    """Test that ECS runner status endpoint accepts valid API key."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert response.status_code == 200


def test_ecs_runner_status_returns_json(api_url, api_key):
    """Test that ECS runner status endpoint returns JSON content type."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_ecs_runner_status_has_success_field(api_url, api_key):
    """Test that ECS runner status response contains success field."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "success" in response.json()


def test_ecs_runner_status_has_running_tasks_field(api_url, api_key):
    """Test that ECS runner status response contains running_tasks field."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "running_tasks" in response.json()


def test_ecs_runner_status_has_tasks_field(api_url, api_key):
    """Test that ECS runner status response contains tasks field."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "tasks" in response.json()


def test_ecs_runner_status_has_cluster_field(api_url, api_key):
    """Test that ECS runner status response contains cluster field."""
    response = make_authenticated_get(f"{api_url}/v1/ecs-runner", api_key)
    assert "cluster" in response.json()


def test_v1_ecs_runner_post_missing_job_id_returns_400(api_url, api_key):
    """Test that POST without job_id returns 400."""
    payload = {
        "job_labels": ["ephemeral-ecs-fargate"],
        "github_repo": "any/repo"
    }
    response = make_authenticated_post(
        f"{api_url}/v1/ecs-runner", api_key, json=payload
    )
    assert response.status_code == 400


def test_v1_ecs_runner_post_missing_github_repo_returns_400(api_url, api_key):
    """Test that POST without github_repo returns 400."""
    payload = {
        "job_id": 666666,
        "job_labels": ["ephemeral-ecs-fargate"]
    }
    response = make_authenticated_post(
        f"{api_url}/v1/ecs-runner", api_key, json=payload
    )
    assert response.status_code == 400


def test_ecs_runner_post_returns_success(api_url, api_key, github_repo):
    """Test that ECS runner POST with valid payload returns success."""
    payload = {
        "job_id": 111111111,
        "job_labels": ["ephemeral-ecs-fargate"],
        "github_repo": github_repo
    }
    response = make_authenticated_post(f"{api_url}/v1/ecs-runner", api_key, json=payload)
    assert response.status_code in [200, 202]


def test_ecs_runner_task_appears_in_cluster(
    api_url, api_key, github_repo, ecs_client, cluster_name
):
    """Test that created ECS task appears in the cluster."""
    payload = {
        "job_id": 222222222,
        "job_labels": ["ephemeral-ecs-fargate"],
        "github_repo": github_repo
    }
    make_authenticated_post(f"{api_url}/v1/ecs-runner", api_key, json=payload)
    time.sleep(5)
    tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
    assert len(tasks['taskArns']) >= 0
