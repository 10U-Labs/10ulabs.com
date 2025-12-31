"""Pytest fixtures for runners/ecs/images post (Docker build) tests."""
import os
import re
from typing import Any, Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.integration import get_aws_account_id_via_cli

POST_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images" / "post"
CONFIG_PATH = POST_DIR / "config.json"
DOCKERFILE_PATH = POST_DIR / "Dockerfile"


def _get_terraform_output_value(output_name: str) -> str:
    """Extract a value from terraform outputs.tf file."""
    shared_outputs = REPO_ROOT / "lib" / "terraform" / "common" / "outputs.tf"
    with open(shared_outputs, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    result = match.group(1) if match else ''
    return result


def _get_terraform_local_value(local_name: str) -> str:
    """Extract a value from terraform locals.tf file."""
    shared_locals = REPO_ROOT / "lib" / "terraform" / "common" / "locals.tf"
    with open(shared_locals, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{local_name}\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    result = match.group(1) if match else ''
    return result


def get_aws_region() -> str:
    """Get AWS region from environment or terraform locals."""
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_local_value("aws_region")
    return region


def get_aws_account_id() -> str:
    """Get AWS account ID using the AWS CLI."""
    return get_aws_account_id_via_cli()


def get_ecr_repository() -> str:
    """Get ECR repository name from terraform outputs."""
    return _get_terraform_output_value("ecr_repository_name_runners")


def get_github_repo() -> str:
    """Get GitHub repository name from terraform outputs."""
    org = _get_terraform_output_value("github_org")
    repo = _get_terraform_output_value("name_for_github_repo")
    return f"{org}/{repo}"


@pytest.fixture(scope="session")
def aws_region() -> str:
    """Fixture providing the AWS region."""
    return get_aws_region()


@pytest.fixture(scope="module")
def aws_account_id() -> str:
    """Fixture providing the AWS account ID."""
    return get_aws_account_id()


@pytest.fixture(scope="module")
def ecr_repository() -> str:
    """Fixture providing the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(scope="module")
def github_repo() -> str:
    """Fixture providing the GitHub repository name."""
    return get_github_repo()


@pytest.fixture(scope="module")
def github_pat() -> str:
    """Fixture providing the GitHub PAT from environment variable."""
    return os.environ.get("GITHUB_PAT", "")


@pytest.fixture(scope="module")
def config() -> Dict[str, Any]:
    """Return the test configuration dictionary."""
    return {
        'aws_region': get_aws_region(),
        'aws_account_id': get_aws_account_id(),
        'ecr_repository': get_ecr_repository(),
        'github_repo': get_github_repo(),
        'post_dir': str(POST_DIR),
        'config_path': str(CONFIG_PATH),
        'dockerfile_path': str(DOCKERFILE_PATH),
    }
