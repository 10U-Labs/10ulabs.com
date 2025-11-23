import json
import os
import subprocess
import pytest
import boto3


@pytest.fixture(scope="module")
def dockerfile_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/api/docker_runner/Dockerfile")


@pytest.fixture(scope="module")
def entrypoint_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/api/docker_runner/entrypoint.py")


@pytest.fixture(scope="module")
def aws_region():
    return os.environ.get("AWS_REGION", "us-east-1")


@pytest.fixture(scope="module")
def aws_account_id():
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


@pytest.fixture(scope="module")
def ecr_repository():
    result = subprocess.run(
        ["grep", "ecr_repository_name", "src/api/terraform.tfvars"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.split('"')[1]


@pytest.fixture(scope="module")
def github_repo():
    return "10ulabs/10ulabs.com"


@pytest.fixture(scope="module")
def github_pat():
    return os.environ.get("GITHUB_PAT")


@pytest.fixture(scope="module")
def docker_image_tag():
    return os.environ.get("TEST_DOCKER_IMAGE_TAG", "github-docker-runner:test")


@pytest.fixture(scope="module")
def docker_image(dockerfile_path, entrypoint_path, docker_image_tag):
    build_context = os.path.dirname(dockerfile_path)

    result = subprocess.run(
        ["docker", "build", "-t", docker_image_tag, "-f", dockerfile_path, build_context],
        check=False,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed: {result.stderr}")

    yield docker_image_tag

    subprocess.run(["docker", "rmi", "-f", docker_image_tag], check=False, capture_output=True)


@pytest.fixture(scope="module")
def image_tag(aws_region, aws_account_id, ecr_repository):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": "available"}]
    )
    return "available"


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


def run_command_in_container(image_tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", image_tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result


def login_to_ecr(aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )


def start_runner_container(ecr_image_uri, repo, name, labels, token):
    process = subprocess.Popen(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", repo,
            "--name", name,
            "--labels", labels,
            "--token", token
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process


def get_github_runners(github_pat, github_repo):
    result = subprocess.run(
        [
            "curl",
            "-H", f"Authorization: token {github_pat}",
            "-H", "Accept: application/vnd.github.v3+json",
            f"https://api.github.com/repos/{github_repo}/actions/runners"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    runners = json.loads(result.stdout)
    return runners.get("runners", [])
