import time
from ..conftest import login_to_ecr
from .conftest import run_runner_and_wait, get_github_runners, find_runner_by_name


def test_runner_status_is_online(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)
    runner_name = f"e2e-test-status-{int(time.time())}"
    run_runner_and_wait(ecr_image_uri, github_repo, runner_name, "e2e-test-status", runner_registration_token)
    runners = get_github_runners(github_pat, github_repo)
    runner = find_runner_by_name(runners, runner_name)
    assert runner["status"] == "online"
