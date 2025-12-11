"""Shared fixtures and utilities for ECS runner image tests."""
import os
import re
import subprocess

import pytest


SHARED_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), '../../../../lib/terraform/modules/shared/outputs.tf'
)
SHARED_LOCALS_PATH = os.path.join(
    os.path.dirname(__file__), '../../../../lib/terraform/modules/shared/locals.tf'
)
BASE_DIR = os.path.join(
    os.path.dirname(__file__), '../../../../src/api/endpoints/image_for_ecs_runners'
)
POST_DIR = os.path.join(BASE_DIR, 'post')
FILES_DIR = POST_DIR  # Backwards compatibility alias
CONFIG_PATH = os.path.join(POST_DIR, 'config.json')
DOCKERFILE_PATH = os.path.join(POST_DIR, 'Dockerfile')
TFVARS_PATH = os.path.join(
    os.path.dirname(__file__), '../../../../src/api/endpoints/ecs_runner/terraform.tfvars'
)


def _get_terraform_output_value(output_name):
    """Extract a value from terraform outputs.tf file."""
    with open(SHARED_MODULE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def _get_terraform_local_value(local_name):
    """Extract a value from terraform locals.tf file."""
    with open(SHARED_LOCALS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{local_name}\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def get_aws_region():
    """Get AWS region from environment or terraform locals."""
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_local_value("aws_region")
    return region


def get_aws_account_id():
    """Get AWS account ID using the AWS CLI."""
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_ecr_repository():
    """Get ECR repository name from terraform outputs."""
    return _get_terraform_output_value("ecr_repository_name_runners")


def get_github_repo():
    """Get GitHub repository name from git remote URL."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True
    )
    url = result.stdout.strip()
    if url.find("github.com") != -1:
        if url.startswith("git@github.com:"):
            repo = url.replace("git@github.com:", "").replace(".git", "")
        elif url.startswith("https://github.com/"):
            repo = url.replace("https://github.com/", "").replace(".git", "")
        else:
            raise ValueError(f"Unexpected GitHub URL format: {url}")
        return repo
    raise ValueError(f"Not a GitHub repository: {url}")


def get_github_pat():
    """Get GitHub PAT from environment variable."""
    try:
        pat = os.environ["GITHUB_PAT"]
    except KeyError:
        pat = None
    return pat


@pytest.fixture(scope="module")
def aws_region():
    """Fixture providing the AWS region."""
    return get_aws_region()


@pytest.fixture(scope="module")
def aws_account_id():
    """Fixture providing the AWS account ID."""
    return get_aws_account_id()


@pytest.fixture(scope="module")
def ecr_repository():
    """Fixture providing the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(scope="module")
def github_repo():
    """Fixture providing the GitHub repository name."""
    return get_github_repo()


@pytest.fixture(scope="module")
def github_pat():
    """Fixture providing the GitHub PAT."""
    return get_github_pat()
