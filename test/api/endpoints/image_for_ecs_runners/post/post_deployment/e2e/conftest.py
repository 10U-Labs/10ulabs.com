"""
E2E test configuration and utilities for ECS runner image lifecycle tests.
"""
import subprocess
import time
import pytest
from ..conftest import login_to_ecr, run_github_api_curl


class RunnerContainer:
    """Wrapper for a Docker container running a GitHub Actions runner."""

    def __init__(self, config):
        """Start a runner container with specified configuration.

        Args:
            config: Dict with keys: uri, repo, name, labels, token
        """
        self.name = config["name"]
        self.container_name = f"runner-{self.name}"
        args = [
            "docker", "run", "--rm", "--init",
            "--name", self.container_name,
            "--platform", "linux/arm64",
            config["uri"],
            "--repo", config["repo"],
            "--name", self.name,
            "--labels", config["labels"],
            "--token", config["token"]
        ]
        self._process = _create_background_process(args)

    def stop(self, timeout=10):
        """Stop the container gracefully using docker stop.

        Returns:
            True if container exited within timeout (graceful), False if SIGKILL was needed.
        """
        start = time.time()
        subprocess.run(
            ["docker", "stop", "-t", str(timeout), self.container_name],
            check=False,
            capture_output=True
        )
        self._process.wait()
        elapsed = time.time() - start
        return elapsed < timeout

    def get_output(self):
        """Get any captured output from the container."""
        if self._process.stdout:
            return self._process.stdout.read().decode('utf-8', errors='replace')
        return ""

    def is_running(self):
        """Check if the container process is still running."""
        return self._process.poll() is None


def _create_background_process(args):
    """Create a background process. Caller is responsible for cleanup."""
    return subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True
    )


def wait_for_process_with_backoff(process, max_attempts=7):
    """
    Wait for a process to complete with exponential backoff.
    """
    attempt = 0
    total_wait = 0
    while attempt < max_attempts:
        wait_time = 2 ** attempt
        returncode = process.poll()
        if returncode is not None:
            return
        time.sleep(wait_time)
        total_wait = total_wait + wait_time
        attempt = attempt + 1
    process.kill()
    process.wait()
    raise subprocess.TimeoutExpired(process.args, total_wait)


def get_github_runners(pat, repo):
    """
    Retrieve the list of GitHub Actions runners for a repository.
    """
    response = run_github_api_curl([
        "curl",
        "-H", f"Authorization: token {pat}",
        "-H", "Accept: application/vnd.github.v3+json",
        f"https://api.github.com/repos/{repo}/actions/runners"
    ])
    try:
        runners = response["runners"]
    except KeyError:
        runners = []
    return runners


def get_runner_and_cleanup(container, pat, repo):
    """
    Get runner information from GitHub and clean up the container.
    """
    time.sleep(30)
    runners = get_github_runners(pat, repo)
    runner = find_runner_by_name(runners, container.name)
    container.stop()
    return runner


def find_runner_by_name(runners, target_name):
    """
    Find a runner in the list by its name.
    """
    index = 0
    while index < len(runners):
        runner = runners[index]
        if runner["name"] == target_name:
            return runner
        index = index + 1
    return None


def runner_exists_with_name(runners, target_name):
    """
    Check if a runner with the specified name exists in the list.
    """
    index = 0
    while index < len(runners):
        runner = runners[index]
        if runner["name"] == target_name:
            return True
        index = index + 1
    return False


def get_label_by_name(labels, target_name):
    """
    Find a label in the list by its name.
    """
    index = 0
    while index < len(labels):
        label = labels[index]
        if label["name"] == target_name:
            return label
        index = index + 1
    return None


def start_runner_and_get_info(config):
    """
    Start a runner container and retrieve its info from GitHub.

    Combines RunnerContainer and get_runner_and_cleanup into a single
    operation to reduce code duplication in tests.

    Args:
        config: Dict with keys: uri, repo, name, labels, token, pat
    """
    container = RunnerContainer(config)
    return get_runner_and_cleanup(container, config["pat"], config["repo"])


def create_shared_runner_context(image_uri, repo, token, region, pat):
    """Create and return a shared runner context for tests."""
    login_to_ecr(region)

    runner_name = f"e2e-test-shared-{int(time.time())}"
    labels = "e2e-label1,e2e-label2,e2e-label3"

    config = {
        "uri": image_uri,
        "repo": repo,
        "name": runner_name,
        "labels": labels,
        "token": token
    }
    container = RunnerContainer(config)

    time.sleep(30)

    runners = get_github_runners(pat, repo)
    runner_info = find_runner_by_name(runners, runner_name)

    return {
        "container": container,
        "name": runner_name,
        "labels": labels,
        "info": runner_info,
        "pat": pat,
        "repo": repo
    }


@pytest.fixture(scope="module")
def shared_runner(
    ecr_image_uri,
    github_repo,
    runner_registration_token,
    aws_region,
    github_pat
):
    """Start a single runner container shared across basic tests."""
    context = create_shared_runner_context(
        ecr_image_uri, github_repo, runner_registration_token, aws_region, github_pat
    )

    yield context

    context["container"].stop()
