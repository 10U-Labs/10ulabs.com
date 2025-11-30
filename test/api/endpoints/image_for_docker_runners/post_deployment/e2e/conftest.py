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
    try:
        token = response["token"]
    except KeyError:
        token = ""
    return token


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
    response = json.loads(result.stdout)
    try:
        runners = response["runners"]
    except KeyError:
        runners = []
    return runners


def get_runner_and_cleanup(process, pat, repo, name):
    time.sleep(30)
    runners = get_github_runners(pat, repo)
    runner = find_runner_by_name(runners, name)
    process.terminate()
    wait_for_process_with_backoff(process)
    return runner


def find_runner_by_name(runners, target_name):
    index = 0
    while index < len(runners):
        runner = runners[index]
        if runner["name"] == target_name:
            return runner
        index = index + 1
    return None


def runner_exists_with_name(runners, target_name):
    index = 0
    while index < len(runners):
        runner = runners[index]
        if runner["name"] == target_name:
            return True
        index = index + 1
    return False


def get_label_by_name(labels, target_name):
    index = 0
    while index < len(labels):
        label = labels[index]
        if label["name"] == target_name:
            return label
        index = index + 1
    return None
