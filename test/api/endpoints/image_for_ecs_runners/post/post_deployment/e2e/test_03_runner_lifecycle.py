"""E2E tests for runner lifecycle management."""
import time
from ..conftest import login_to_ecr
from .conftest import (
    RunnerContainer,
    get_github_runners,
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

    config = {
        "uri": ecr_image_uri,
        "repo": github_repo,
        "name": runner_name,
        "labels": "e2e-sigterm",
        "token": runner_registration_token,
        "pat": github_pat
    }
    container = RunnerContainer(config)

    time.sleep(30)

    container.stop()

    time.sleep(10)

    runners = get_github_runners(github_pat, github_repo)
    exists = runner_exists_with_name(runners, runner_name)

    assert not exists
