import json
import subprocess
import time
import pytest
import boto3


@pytest.fixture(scope="module")
def image_tag(aws_region, ecr_repository):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": "available"}]
    )
    tags = response["imageDetails"][0].get("imageTags", [])
    available_tag = next((tag for tag in tags if tag == "available"), None)
    if not available_tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return available_tag


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository, image_tag):
    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:{image_tag}"


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


def login_to_ecr(region):
    password_result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True,
        capture_output=True,
        text=True
    )
    ecr_url = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=True,
        capture_output=True,
        text=True
    )
    account_id = ecr_url.stdout.strip()
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin",
         f"{account_id}.dkr.ecr.{region}.amazonaws.com"],
        input=password_result.stdout,
        check=True,
        text=True
    )


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
