import json
import os
import subprocess
import pytest
import boto3


def get_dockerfile_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/api/docker_runner/Dockerfile")


def get_aws_region():
    return os.environ.get("AWS_REGION", "us-east-1")


def get_aws_account_id():
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_ecr_repository():
    result = subprocess.run(
        ["grep", "ecr_repository_name", "src/api/terraform.tfvars"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.split('"')[1]


def get_github_repo():
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True
    )
    url = result.stdout.strip()
    if "github.com" in url:
        if url.startswith("git@github.com:"):
            repo = url.replace("git@github.com:", "").replace(".git", "")
        elif url.startswith("https://github.com/"):
            repo = url.replace("https://github.com/", "").replace(".git", "")
        else:
            raise ValueError(f"Unexpected GitHub URL format: {url}")
        return repo
    raise ValueError(f"Not a GitHub repository: {url}")


def get_github_pat():
    return os.environ.get("GITHUB_PAT")


def get_docker_image_tag():
    return os.environ.get("TEST_DOCKER_IMAGE_TAG", "github-docker-runner:test")


@pytest.fixture(scope="module")
def dockerfile_path():
    return get_dockerfile_path()


@pytest.fixture(scope="module")
def aws_region():
    return get_aws_region()


@pytest.fixture(scope="module")
def aws_account_id():
    return get_aws_account_id()


@pytest.fixture(scope="module")
def ecr_repository():
    return get_ecr_repository()


@pytest.fixture(scope="module")
def github_repo():
    return get_github_repo()


@pytest.fixture(scope="module")
def github_pat():
    return get_github_pat()


@pytest.fixture(scope="module")
def docker_image_tag():
    return get_docker_image_tag()


@pytest.fixture(scope="module")
def docker_image():
    path = get_dockerfile_path()
    tag = get_docker_image_tag()
    build_context = os.path.dirname(path)

    result = subprocess.run(
        ["docker", "build", "-t", tag, "-f", path, build_context],
        check=False,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed: {result.stderr}")

    yield tag

    subprocess.run(["docker", "rmi", "-f", tag], check=False, capture_output=True)


@pytest.fixture(scope="module")
def image_tag():
    region = get_aws_region()
    repository = get_ecr_repository()
    client = boto3.client("ecr", region_name=region)
    response = client.describe_images(
        repositoryName=repository,
        imageIds=[{"imageTag": "available"}]
    )
    tags = response["imageDetails"][0].get("imageTags", [])
    available_tag = next((tag for tag in tags if tag == "available"), None)
    if not available_tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return available_tag


@pytest.fixture(scope="module")
def ecr_image_uri():
    region = get_aws_region()
    account_id = get_aws_account_id()
    repository = get_ecr_repository()
    tag = get_image_tag()
    return f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository}:{tag}"


@pytest.fixture(scope="module")
def runner_registration_token():
    pat = get_github_pat()
    repo = get_github_repo()
    result = subprocess.run(
        [
            "curl",
            "-X", "POST",
            "-H", f"Authorization: token {pat}",
            "-H", "Accept: application/vnd.github.v3+json",
            f"https://api.github.com/repos/{repo}/actions/runners/registration-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    response = json.loads(result.stdout)
    return response.get("token", "")


def get_image_tag():
    region = get_aws_region()
    repository = get_ecr_repository()
    client = boto3.client("ecr", region_name=region)
    response = client.describe_images(
        repositoryName=repository,
        imageIds=[{"imageTag": "available"}]
    )
    tags = response["imageDetails"][0].get("imageTags", [])
    available_tag = next((tag for tag in tags if tag == "available"), None)
    if not available_tag:
        raise ValueError("Image with tag 'available' not found in ECR")
    return available_tag


def run_command_in_container(tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result


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
