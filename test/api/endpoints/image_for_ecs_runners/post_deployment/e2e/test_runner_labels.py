"""E2E tests for ECS runner label configuration."""
import time
from ..conftest import login_to_ecr
from .conftest import start_runner_container, get_runner_and_cleanup, get_label_by_name


def test_runner_has_correct_labels(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    """Test that a runner registers with the specified custom label."""
    login_to_ecr(aws_region)
    runner_name = f"e2e-test-labels-{int(time.time())}"
    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "e2e-custom-label,docker", runner_registration_token)
    runner = get_runner_and_cleanup(process, github_pat, github_repo, runner_name)
    labels = runner["labels"]
    label = get_label_by_name(labels, "e2e-custom-label")
    assert label is not None


def test_runner_has_all_specified_labels(ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat):
    """Test that a runner registers with multiple custom labels."""
    login_to_ecr(aws_region)
    runner_name = f"e2e-test-multi-labels-{int(time.time())}"
    process = start_runner_container(ecr_image_uri, github_repo, runner_name, "label1,label2,label3", runner_registration_token)
    runner = get_runner_and_cleanup(process, github_pat, github_repo, runner_name)
    labels = runner["labels"]
    label = get_label_by_name(labels, "label1")
    assert label is not None
