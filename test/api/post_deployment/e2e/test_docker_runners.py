import time
import pytest
import requests
from botocore.exceptions import ClientError
from .conftest import make_authenticated_post, make_authenticated_get


@pytest.fixture(name="stable_ecr_image_exists", scope="module")
def stable_ecr_image_exists_fixture(ecr_image_count):
    return ecr_image_count > 0


def wait_for_task_running(ecs_client, cluster_name, task_arn, timeout=120):
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        if not response['tasks']:
            return False
        status = response['tasks'][0]['lastStatus']
        if status == 'RUNNING':
            return True
        if status in ('STOPPED', 'DEPROVISIONING'):
            return False
        time.sleep(5)
    return False


def stop_task_safely(ecs_client, cluster_name, task_arn):
    try:
        ecs_client.stop_task(cluster=cluster_name, task=task_arn)
    except ClientError:
        pass


@pytest.fixture(name="test_fargate_task", scope="module")
def test_fargate_task_fixture(
    api_url, api_key, github_repo, ecr_image_count, ecs_client, config
):
    if ecr_image_count == 0:
        yield None
        return
    job_id = int(time.time())
    payload = {
        "job_id": job_id,
        "job_labels": ["ephemeral-ecs-fargate-spot"],
        "github_repo": github_repo
    }
    response = make_authenticated_post(
        f"{api_url}/v1/docker-runner", api_key, json=payload
    )
    if response.status_code not in [200, 202]:
        yield None
        return
    data = response.json()
    task_arn = data.get("task_arn")
    if not task_arn:
        yield None
        return
    cluster_name = config["cluster_name"]
    wait_for_task_running(ecs_client, cluster_name, task_arn)
    yield {
        "task_arn": task_arn,
        "job_id": job_id,
        "github_repo": github_repo,
        "cluster_name": cluster_name
    }
    stop_task_safely(ecs_client, cluster_name, task_arn)


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


def test_docker_runner_endpoint_returns_images_when_available(
    api_url, api_key, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    response = make_authenticated_get(
        f"{api_url}/v1/image-for-docker-runners/latest", api_key
    )
    assert response.status_code == 200


def test_docker_runner_endpoint_returns_error_when_no_images(
    api_url, api_key, stable_ecr_image_exists
):
    if stable_ecr_image_exists:
        pytest.skip("Stable ECR image exists")
    response = make_authenticated_get(
        f"{api_url}/v1/image-for-docker-runners/latest", api_key
    )
    assert response.status_code in [404, 500]


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


def test_docker_runner_post_returns_task_arn(test_fargate_task, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    assert test_fargate_task is not None
    assert test_fargate_task.get("task_arn") is not None


def test_docker_runner_task_reaches_running_state(
    test_fargate_task, ecs_client, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    cluster_name = test_fargate_task.get("cluster_name")
    response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
    status = response['tasks'][0]['lastStatus']
    assert status == 'RUNNING'


def test_docker_runner_task_has_type_tag(
    test_fargate_task, ecs_client, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    cluster_name = test_fargate_task.get("cluster_name")
    response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
    tags = response['tasks'][0].get('tags', [])
    tag_dict = {tag['key']: tag['value'] for tag in tags}
    assert tag_dict.get("Type") == "ephemeral-runner"


def test_docker_runner_task_has_managed_by_tag(
    test_fargate_task, ecs_client, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    cluster_name = test_fargate_task.get("cluster_name")
    response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
    tags = response['tasks'][0].get('tags', [])
    tag_dict = {tag['key']: tag['value'] for tag in tags}
    assert tag_dict.get("ManagedBy") == "docker-runner-api"


def test_docker_runner_task_has_job_id_tag(
    test_fargate_task, ecs_client, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    cluster_name = test_fargate_task.get("cluster_name")
    job_id = test_fargate_task.get("job_id")
    response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
    tags = response['tasks'][0].get('tags', [])
    tag_dict = {tag['key']: tag['value'] for tag in tags}
    assert tag_dict.get("GitHubJobId") == str(job_id)


def test_docker_runner_task_has_repo_tag(
    test_fargate_task, ecs_client, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    cluster_name = test_fargate_task.get("cluster_name")
    github_repo = test_fargate_task.get("github_repo")
    response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
    tags = response['tasks'][0].get('tags', [])
    tag_dict = {tag['key']: tag['value'] for tag in tags}
    assert tag_dict.get("GitHubRepo") == github_repo


def test_docker_runner_appears_in_status_endpoint(
    test_fargate_task, api_url, api_key, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    status_response = make_authenticated_get(f"{api_url}/v1/docker-runner", api_key)
    tasks = status_response.json().get("tasks", [])
    task_arns = [task.get("task_arn") for task in tasks]
    assert task_arn in task_arns
