"""E2E test for runner registration with invalid token."""
import subprocess
from ..conftest import login_to_ecr


def test_runner_fails_with_invalid_registration_token(
    ecr_image_uri,
    github_repo,
    aws_region
):
    """Test that a runner fails to register with an invalid token."""
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
