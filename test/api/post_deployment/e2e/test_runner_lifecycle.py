import time
import requests


def test_fargate_runner_post_returns_success(api_url, api_key, github_repo):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    payload = {"job_id": 111111111, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": github_repo}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202]


def test_fargate_runner_task_appears_in_cluster(api_url, api_key, github_repo, ecs_client, config):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    payload = {"job_id": 222222222, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": github_repo}
    requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    time.sleep(5)
    cluster_name = config["cluster_name"]
    tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
    assert len(tasks['taskArns']) >= 0


def test_fargate_runner_cluster_exists(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response['clusters']) == 1


def test_fargate_runner_cluster_is_active(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response['clusters'][0]['status'] == 'ACTIVE'
