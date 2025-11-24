import subprocess
import time
from conftest import login_to_ecr, start_runner_container, get_github_runners, wait_for_process_with_backoff


def test_runner_fails_with_invalid_registration_token(ecr_image_uri, github_repo, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "--platform", "linux/arm64",
            ecr_image_uri,
            "--repo", github_repo,
            "--name", "e2e-test-runner-invalid",
            "--labels", "e2e-test",
            "--token", "invalid-token-12345"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 1


def test_runner_successfully_registers_with_github(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-runner-{int(time.time())}"

    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "e2e-test-ephemeral", runner_registration_token)

    time.sleep(30)

    runners = get_github_runners(github_pat, github_repo)
    runner_names = [r["name"] for r in runners]

    process.terminate()
    wait_for_process_with_backoff(process)

    assert runner_name in runner_names


def test_runner_appears_online_in_github(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-runner-online-{int(time.time())}"

    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "e2e-test-online", runner_registration_token)

    time.sleep(30)

    runners = get_github_runners(github_pat, github_repo)
    matching_runners = [r for r in runners if r["name"] == runner_name]

    process.terminate()
    wait_for_process_with_backoff(process)

    assert len(matching_runners) == 1
