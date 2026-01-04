"""End-to-end tests for ECS runner functionality."""
import time

import pytest

from ..conftest import (
    create_runner_job_payload,
    ECS_RUNNER_REQUEST_TIMEOUT,
    get_ecs_task_tags,
    make_e2e_get,
    make_e2e_post,
)


@pytest.fixture(name="stable_ecr_image_exists", scope="module")
def stable_ecr_image_exists_fixture(ecr_image_count):
    """Return whether a stable ECR image exists for testing."""
    return ecr_image_count > 0


@pytest.fixture(name="ecs_context", scope="module")
def ecs_context_fixture(ecs_client, cluster_name):
    """Provide ECS client and cluster name context."""
    return {"client": ecs_client, "cluster_name": cluster_name}


def wait_for_task_running(ecs_client, cluster_name, task_arn, timeout=120):
    """Wait for an ECS task to reach RUNNING state."""
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


def stop_task(ecs_client, cluster_name, task_arn):
    """Stop an ECS task."""
    ecs_client.stop_task(cluster=cluster_name, task=task_arn)


@pytest.fixture(name="test_fargate_task", scope="module")
def test_fargate_task_fixture(test_context, ecr_image_count, ecs_context, config):
    """Create a test Fargate task and clean it up after tests."""
    if ecr_image_count == 0:
        print("Skipping ECS runner test: ecr_image_count is 0")
        yield None
        return
    runner_labels = config['fargate_e2e_test']
    job_id, payload = create_runner_job_payload(
        test_context["github_repo"], runner_labels, test_context["github_run_id"]
    )
    response = make_e2e_post(
        f"{test_context['api_credentials']['url']}/v1/runners/ecs",
        test_context["api_credentials"]["key"],
        json=payload,
        timeout=ECS_RUNNER_REQUEST_TIMEOUT
    )
    if response.status_code not in [200, 202]:
        print(f"ECS runner POST failed: status={response.status_code}, body={response.text}")
        yield None
        return
    response_json = response.json()
    task_arn = response_json.get("task_arn")
    if not task_arn:
        print(f"ECS runner POST returned no task_arn: {response_json}")
        yield None
        return
    wait_for_task_running(ecs_context["client"], ecs_context["cluster_name"], task_arn)
    yield {
        "task_arn": task_arn,
        "job_id": job_id,
        "github_repo": test_context["github_repo"],
        "cluster_name": ecs_context["cluster_name"],
        "run_id": test_context["github_run_id"]
    }
    stop_task(ecs_context["client"], ecs_context["cluster_name"], task_arn)
    assert True  # Explicit pass


def test_ecs_runner_post_returns_response(test_fargate_task, stable_ecr_image_exists):
    """Test that ECS runner POST returns a response."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    assert test_fargate_task is not None


def test_ecs_runner_post_response_has_task_arn(test_fargate_task, stable_ecr_image_exists):
    """Test that ECS runner POST response has task ARN."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    assert test_fargate_task.get("task_arn") is not None


def test_ecs_runner_task_reaches_running_state(
    test_fargate_task, ecs_context, stable_ecr_image_exists
):
    """Test that ECS runner task reaches RUNNING state."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    response = ecs_context["client"].describe_tasks(
        cluster=test_fargate_task.get("cluster_name"),
        tasks=[test_fargate_task.get("task_arn")]
    )
    assert response['tasks'][0]['lastStatus'] == 'RUNNING'


def test_ecs_runner_task_has_type_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    """Test that ECS runner task has Type tag."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"],
        test_fargate_task.get("cluster_name"),
        test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("Type") == "workflow-runner"


def test_ecs_runner_task_has_managed_by_tag(
    test_fargate_task, ecs_context, stable_ecr_image_exists
):
    """Test that ECS runner task has ManagedBy tag."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"],
        test_fargate_task.get("cluster_name"),
        test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("ManagedBy") == "ecs-runner-api"


def test_ecs_runner_task_has_job_id_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    """Test that ECS runner task has GitHubJobId tag."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"],
        test_fargate_task.get("cluster_name"),
        test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("GitHubJobId") == str(test_fargate_task.get("job_id"))


def test_ecs_runner_task_has_repo_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    """Test that ECS runner task has GitHubRepo tag."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"],
        test_fargate_task.get("cluster_name"),
        test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("GitHubRepo") == test_fargate_task.get("github_repo")


def test_ecs_runner_appears_in_status_endpoint(
    test_fargate_task, api_url, api_key, stable_ecr_image_exists
):
    """Test that ECS runner task appears in status endpoint."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    task_arn = test_fargate_task.get("task_arn")
    status_response = make_e2e_get(f"{api_url}/v1/runners/ecs", api_key)
    tasks = status_response.json().get("tasks", [])
    task_arns = [task.get("task_arn") for task in tasks]
    assert task_arn in task_arns


def test_ecs_runner_task_has_run_id_tag(test_fargate_task, ecs_context, stable_ecr_image_exists):
    """Test that ECS runner task has RunId tag."""
    if not stable_ecr_image_exists:
        pytest.skip("No stable ECR image available")
    if test_fargate_task is None:
        pytest.fail("Test task not created")
    run_id = test_fargate_task.get("run_id")
    tag_dict = get_ecs_task_tags(
        ecs_context["client"],
        test_fargate_task.get("cluster_name"),
        test_fargate_task.get("task_arn")
    )
    assert tag_dict.get("RunId") == str(run_id)
