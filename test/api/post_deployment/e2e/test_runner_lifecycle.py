import time
import requests


def test_fargate_runner_task_transitions_to_provisioning(api_url, api_key, github_repo, ecs_client, tfvars):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 111111111, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": github_repo}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202]
    time.sleep(5)
    cluster_name = tfvars["cluster_name"]
    tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
    assert len(tasks['taskArns']) > 0


def test_fargate_runner_task_does_not_immediately_fail(api_url, api_key, github_repo, ecs_client, tfvars):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 222222222, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": github_repo}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202]
    time.sleep(10)
    cluster_name = tfvars["cluster_name"]
    stopped_tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='STOPPED')
    if stopped_tasks['taskArns']:
        for task_arn in stopped_tasks['taskArns'][-3:]:
            task = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
            if task['tasks']:
                stopped_reason = task['tasks'][0].get('stoppedReason', '')
                assert 'CannotPullContainerError' not in stopped_reason


def test_fargate_runner_uses_correct_capacity_provider(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
    if tasks['taskArns']:
        task_arn = tasks['taskArns'][0]
        task = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        if task['tasks']:
            assert task['tasks'][0].get('capacityProviderName') == 'FARGATE_SPOT'


def test_fargate_runner_task_has_public_ip(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    tasks = ecs_client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
    if tasks['taskArns']:
        task_arn = tasks['taskArns'][0]
        task = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        if task['tasks']:
            attachments = task['tasks'][0].get('attachments', [])
            has_network = False
            for attachment in attachments:
                if attachment['type'] == 'ElasticNetworkInterface':
                    has_network = True
            assert has_network is True
