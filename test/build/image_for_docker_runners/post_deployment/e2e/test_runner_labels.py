import time
from ..conftest import login_to_ecr
from .conftest import start_runner_container, get_github_runners, wait_for_process_with_backoff


def test_runner_has_correct_labels(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-labels-{int(time.time())}"

    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "e2e-custom-label,docker", runner_registration_token)

    time.sleep(30)

    runners = get_github_runners(github_pat, github_repo)
    matching_runners = [r for r in runners if r["name"] == runner_name]
    label_names = [label["name"] for label in matching_runners[0].get("labels", [])]

    process.terminate()
    wait_for_process_with_backoff(process)

    assert "e2e-custom-label" in label_names


def test_runner_has_all_specified_labels(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-multi-labels-{int(time.time())}"

    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "label1,label2,label3", runner_registration_token)

    time.sleep(30)

    runners = get_github_runners(github_pat, github_repo)
    matching_runners = [r for r in runners if r["name"] == runner_name]
    label_names = [label["name"] for label in matching_runners[0].get("labels", [])]

    process.terminate()
    wait_for_process_with_backoff(process)

    assert "label1" in label_names
