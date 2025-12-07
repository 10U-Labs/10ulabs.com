"""E2E tests for ECS runner label configuration."""
import time
from ..conftest import login_to_ecr
from .conftest import start_runner_and_get_info, get_label_by_name


def test_runner_has_correct_labels(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region,
    github_pat
):
    """Test that a runner registers with the specified custom label."""
    login_to_ecr(aws_region)
    runner = start_runner_and_get_info({
        "uri": ecr_image_uri, "repo": github_repo,
        "name": f"e2e-test-labels-{int(time.time())}",
        "labels": "e2e-custom-label,docker",
        "token": runner_registration_token, "pat": github_pat
    })
    labels = runner["labels"]
    label = get_label_by_name(labels, "e2e-custom-label")
    assert label is not None


def test_runner_has_all_specified_labels(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region,
    github_pat
):
    """Test that a runner registers with multiple custom labels."""
    login_to_ecr(aws_region)
    runner = start_runner_and_get_info({
        "uri": ecr_image_uri, "repo": github_repo,
        "name": f"e2e-test-multi-labels-{int(time.time())}",
        "labels": "label1,label2,label3",
        "token": runner_registration_token, "pat": github_pat
    })
    labels = runner["labels"]
    label = get_label_by_name(labels, "label1")
    assert label is not None
