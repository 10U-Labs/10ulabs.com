from test.api.post_deployment.conftest import (
    create_runner_job_payload,
    get_ecs_task_tags,
    make_e2e_get,
    make_e2e_post,
)
import time
import pytest
from botocore.exceptions import ClientError


@pytest.fixture(name="stable_ecr_image_exists", scope="module")
def stable_ecr_image_exists_fixture(ecr_image_count):
    return ecr_image_count > 0


@pytest.fixture(name="ecs_context", scope="module")
def ecs_context_fixture(ecs_client, cluster_name):
    return {"client": ecs_client, "cluster_name": cluster_name}


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
def test_fargate_task_fixture(api_credentials, github_repo, ecr_image_count, ecs_context, config):
    if ecr_image_count == 0:
        yield None
        return
    runner_label = config['runner_label_fargate_spot_e2e_test']
    job_id, payload = create_runner_job_payload(github_repo, [runner_label])
    response = make_e2e_post(
        f"{api_credentials['url']}/v1/docker-runner", api_credentials["key"], json=payload
    )
    if response.status_code not in [200, 202]:
        yield None
        return
    task_arn = response.json().get("task_arn")
    if not task_arn:
        yield None
        return
    wait_for_task_running(ecs_context["client"], ecs_context["cluster_name"], task_arn)
    yield {"task_arn": task_arn, "job_id": job_id, "github_repo": github_repo, "cluster_name": ecs_context["cluster_name"]}
    stop_task_safely(ecs_context["client"], ecs_context["cluster_name"], task_arn)


def test_docker_runner_post_returns_task_arn(test_fargate_task, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    assert test_fargate_task is not None
    assert test_fargate_task.get("task_arn") is not None


def test_docker_runner_task_reaches_running_state(test_fargate_task, ecs_context, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    response = ecs_context["client"].describe_tasks(
        cluster=test_fargate_task.get("cluster_name"), tasks=[test_fargate_task.get("task_arn")]
    )
    assert response['tasks'][0]['lastStatus'] == 'RUNNING'


def test_docker_runner_task_has_type_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"], test_fargate_task.get("cluster_name"), test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("Type") == "workflow-runner"


def test_docker_runner_task_has_managed_by_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"], test_fargate_task.get("cluster_name"), test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("ManagedBy") == "docker-runner-api"


def test_docker_runner_task_has_job_id_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"], test_fargate_task.get("cluster_name"), test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("GitHubJobId") == str(test_fargate_task.get("job_id"))


def test_docker_runner_task_has_repo_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"], test_fargate_task.get("cluster_name"), test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("GitHubRepo") == test_fargate_task.get("github_repo")


def test_docker_runner_appears_in_status_endpoint(
    test_fargate_task, api_url, api_key, stable_ecr_image_exists
):
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    status_response = make_e2e_get(f"{api_url}/v1/docker-runner", api_key)
    tasks = status_response.json().get("tasks", [])
    task_arns = [task.get("task_arn") for task in tasks]
    assert task_arn in task_arns
