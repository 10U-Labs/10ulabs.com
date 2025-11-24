import os
import subprocess
import pytest


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
