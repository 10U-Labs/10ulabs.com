import os
import re
import subprocess
import pytest


SHARED_MODULE_PATH = os.path.join(os.path.dirname(__file__), '../../src/modules/shared/outputs.tf')
BASE_DIR = os.path.join(os.path.dirname(__file__), '../../src/image_for_docker_runners')
FILES_DIR = os.path.join(BASE_DIR, 'files')
CONFIG_PATH = os.path.join(FILES_DIR, 'config.yml')
DOCKERFILE_PATH = os.path.join(FILES_DIR, 'Dockerfile')
TFVARS_PATH = os.path.join(os.path.dirname(__file__), '../../src/api/terraform.tfvars')


def _get_terraform_output_value(output_name):
    with open(SHARED_MODULE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def get_aws_region():
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_output_value("aws_region")
    return region


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
    try:
        pat = os.environ["GITHUB_PAT"]
    except KeyError:
        pat = None
    return pat


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
