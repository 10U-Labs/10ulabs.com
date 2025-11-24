import json
import subprocess
import time
import pytest


@pytest.fixture(scope="module")
def runner_registration_token(github_pat, github_repo):
    result = subprocess.run(
        [
            "curl",
            "-X", "POST",
            "-H", f"Authorization: token {github_pat}",
            "-H", "Accept: application/vnd.github.v3+json",
            f"https://api.github.com/repos/{github_repo}/actions/runners/registration-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    response = json.loads(result.stdout)
    return response.get("token", "")


def start_runner_container(uri, repo, name, labels, token):
    args = [
        "docker", "run", "--rm",
        "--platform", "linux/arm64",
        uri,
        "--repo", repo,
        "--name", name,
        "--labels", labels,
        "--token", token
    ]
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        close_fds=True
    )


def wait_for_process_with_backoff(process, max_attempts=7):
    for attempt in range(max_attempts):
        wait_time = 2 ** attempt
        returncode = process.poll()
        if returncode is not None:
            return
        time.sleep(wait_time)
    process.kill()
    process.wait()
    raise subprocess.TimeoutExpired(process.args, sum(2**i for i in range(max_attempts)))


def get_github_runners(pat, repo):
    result = subprocess.run(
        [
            "curl",
            "-H", f"Authorization: token {pat}",
            "-H", "Accept: application/vnd.github.v3+json",
            f"https://api.github.com/repos/{repo}/actions/runners"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    runners = json.loads(result.stdout)
    return runners.get("runners", [])


def run_runner_and_wait(uri, repo, name, labels, token):
    process = start_runner_container(uri, repo, name, labels, token)
    time.sleep(30)
    process.terminate()
    wait_for_process_with_backoff(process)


def get_matching_runner(pat, repo, name):
    runners = get_github_runners(pat, repo)
    return [r for r in runners if r["name"] == name]
