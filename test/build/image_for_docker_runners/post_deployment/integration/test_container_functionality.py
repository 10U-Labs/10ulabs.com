import subprocess


def test_container_starts_with_missing_args(docker_image):
    result = subprocess.run(
        ["docker", "run", "--rm", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.returncode != 0


def test_entrypoint_prints_registration_message(docker_image):
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
    assert "Registering GitHub Actions runner..." in result.stdout


def test_entrypoint_prints_repository_from_arguments(docker_image):
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
    assert "Repository: myorg/myrepo" in result.stdout


def test_entrypoint_prints_runner_name_from_arguments(docker_image):
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
    assert "Runner Name: my-test-runner" in result.stdout


def test_entrypoint_prints_labels_from_arguments(docker_image):
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
    assert "Labels: custom-label,another-label" in result.stdout


def test_entrypoint_fails_with_invalid_token(docker_image):
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
