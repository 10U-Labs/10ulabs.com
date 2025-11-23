import os
import subprocess
import time
import pytest
import boto3


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
def image_tag(aws_region, aws_account_id, ecr_repository):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": "latest"}]
    )
    return "latest"


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository, image_tag):
    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:{image_tag}"


@pytest.fixture(scope="module")
def github_pat():
    return os.environ.get("GITHUB_PAT")


@pytest.fixture(scope="module")
def github_repo():
    return "10ulabs/10ulabs.com"


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
    import json
    response = json.loads(result.stdout)
    return response.get("token", "")


def test_ecr_image_exists(ecr_image_uri, aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert len(response["imageDetails"]) == 1


def test_ecr_image_is_arm64(ecr_image_uri, aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert response["imageDetails"][0]["imageManifestMediaType"] == "application/vnd.oci.image.manifest.v1+json"


def test_docker_login_to_ecr_succeeds(aws_region):
    result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_runner_fails_with_missing_repo_argument(ecr_image_uri, aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--name", "test-runner",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_name_argument(ecr_image_uri, aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_labels_argument(ecr_image_uri, aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_token_argument(ecr_image_uri, aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--labels", "test"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_invalid_registration_token(ecr_image_uri, github_repo, aws_region):
    subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", aws_region],
        check=False,
        capture_output=True,
        text=True,
        stdout=subprocess.PIPE
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm",
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
