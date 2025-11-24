import subprocess
from conftest import login_to_ecr


def test_runner_fails_with_missing_repo_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--name", "test-runner",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_name_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_labels_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_token_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--labels", "test"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
