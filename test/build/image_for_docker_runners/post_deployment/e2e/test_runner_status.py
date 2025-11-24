import time
from conftest import login_to_ecr, start_runner_container, get_github_runners, wait_for_process_with_backoff


def test_runner_status_is_online(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-status-{int(time.time())}"

    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "e2e-test-status", runner_registration_token)

    time.sleep(30)

    runners = get_github_runners(github_pat, github_repo)
    matching_runners = [r for r in runners if r["name"] == runner_name]

    process.terminate()
    wait_for_process_with_backoff(process)

    assert matching_runners[0]["status"] == "online"
