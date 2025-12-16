"""E2E tests for runner lifecycle management."""
import time
from ..conftest import login_to_ecr
from .conftest import (
    start_runner_container,
    get_github_runners,
    wait_for_process_with_backoff,
    runner_exists_with_name
)


def test_runner_cleanup_on_sigterm(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region,
    github_pat
):
    """Test that runner properly cleans up and deregisters on SIGTERM."""
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-sigterm-{int(time.time())}"

    process = start_runner_container(
        ecr_image_uri,
        github_repo,
        runner_name,
        "e2e-sigterm",
        runner_registration_token
    )

    time.sleep(30)

    process.terminate()
    wait_for_process_with_backoff(process)

    time.sleep(10)

    runners = get_github_runners(github_pat, github_repo)
    exists = runner_exists_with_name(runners, runner_name)

    assert not exists
