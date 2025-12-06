"""Tests for container functionality in ECS runner image."""
import subprocess


def test_container_starts_with_missing_args(docker_image):
    """Test that container fails when started with missing arguments."""
    result = subprocess.run(
        ["docker", "run", "--rm", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.returncode != 0


def test_entrypoint_prints_registration_message(docker_image):
    """Test that entrypoint prints registration message."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    expected = "Registering GitHub Actions runner..."
    start_index = result.stdout.find(expected)
    assert start_index != -1


def test_entrypoint_prints_repository_from_arguments(docker_image):
    """Test that entrypoint prints repository from arguments."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "myorg/myrepo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    expected = "Repository: myorg/myrepo"
    start_index = result.stdout.find(expected)
    assert start_index != -1


def test_entrypoint_prints_runner_name_from_arguments(docker_image):
    """Test that entrypoint prints runner name from arguments."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "my-test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    expected = "Runner Name: my-test-runner"
    start_index = result.stdout.find(expected)
    assert start_index != -1


def test_entrypoint_prints_labels_from_arguments(docker_image):
    """Test that entrypoint prints labels from arguments."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "custom-label,another-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    expected = "Labels: custom-label,another-label"
    start_index = result.stdout.find(expected)
    assert start_index != -1


def test_entrypoint_fails_with_invalid_token(docker_image):
    """Test that entrypoint fails with invalid token."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "invalid-token-123"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 1
