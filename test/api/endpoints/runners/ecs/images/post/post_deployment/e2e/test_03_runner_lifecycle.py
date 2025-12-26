"""E2E tests for runner lifecycle management."""
import time
from ..conftest import login_to_ecr
from .conftest import RunnerContainer


def test_runner_graceful_shutdown_on_sigterm(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region
):
    """Test that runner handles SIGTERM gracefully and exits within timeout.

    This verifies the container responds to SIGTERM (sent by docker stop)
    and exits cleanly without requiring SIGKILL. In production, the
    runner_cleanup Lambda handles deregistering stale runners from GitHub.
    """
    login_to_ecr(aws_region)

    runner_name = f"e2e-test-sigterm-{int(time.time())}"

    config = {
        "uri": ecr_image_uri,
        "repo": github_repo,
        "name": runner_name,
        "labels": "e2e-sigterm",
        "token": runner_registration_token
    }
    container = RunnerContainer(config)

    time.sleep(30)

    exited_gracefully = container.stop(timeout=10)

    if not exited_gracefully:
        output = container.get_output()
        print(f"Container output:\n{output}")

    assert exited_gracefully, "Container did not respond to SIGTERM within timeout"
