"""E2E tests for ECS runner status verification."""
import time
from ..conftest import login_to_ecr
from .conftest import start_runner_container, get_runner_and_cleanup


def test_runner_status_is_online(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region,
    github_pat
):
    """Test that a runner registers and shows online status in GitHub."""
    login_to_ecr(aws_region)
    runner_name = f"e2e-test-status-{int(time.time())}"
    process = start_runner_container(
        ecr_image_uri,
        github_repo,
        runner_name,
        "e2e-test-status",
        runner_registration_token
    )
    runner = get_runner_and_cleanup(
        process,
        github_pat,
        github_repo,
        runner_name
    )
    assert runner["status"] == "online"
