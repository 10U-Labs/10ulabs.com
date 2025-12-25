"""Shared fixtures and utilities for ECS runner image tests."""
import os

import pytest
from repo_utils import REPO_ROOT
from terraform_config import get_shared_config

# Path constants for backwards compatibility
BASE_DIR = str(REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners")
POST_DIR = os.path.join(BASE_DIR, 'post')
FILES_DIR = POST_DIR  # Backwards compatibility alias
CONFIG_PATH = os.path.join(POST_DIR, 'config.json')
DOCKERFILE_PATH = os.path.join(POST_DIR, 'Dockerfile')
TFVARS_PATH = os.path.join(BASE_DIR, 'terraform.tfvars')


def get_aws_region():
    """Get AWS region from environment or terraform config."""
    try:
        return os.environ["AWS_REGION"]
    except KeyError:
        return get_shared_config()["aws_region"]


def get_aws_account_id():
    """Get AWS account ID using the AWS CLI."""
    from test_fixtures.integration import get_aws_account_id_via_cli
    return get_aws_account_id_via_cli()


def get_ecr_repository():
    """Get ECR repository name from terraform config."""
    return get_shared_config()["ecr_repository_name_runners"]


def get_github_repo():
    """Get GitHub repository name from terraform config."""
    config = get_shared_config()
    return f"{config['github_org']}/{config['name_for_github_repo']}"


def get_github_pat():
    """Get GitHub PAT from environment variable."""
    return os.environ.get("GITHUB_PAT")


# Note: aws_region fixture is inherited from test/api/conftest.py -> test_fixtures.aws
# Do not redefine it here.


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
