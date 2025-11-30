import os
import re
import subprocess
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
POST_DIR = ENDPOINT_SRC / "post"
CONFIG_PATH = POST_DIR / "config.yml"
SHARED_MODULE_PATH = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
TFVARS_PATH = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"


def _get_terraform_output_value(output_name: str) -> str:
    with open(SHARED_MODULE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    result = match.group(1) if match else ''
    return result


def get_aws_region() -> str:
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_output_value("aws_region")
    return region


def get_aws_account_id() -> str:
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_github_repo() -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True
    )
    url = result.stdout.strip()
    repo = ''
    if url.find("github.com") != -1:
        if url.startswith("git@github.com:"):
            repo = url.replace("git@github.com:", "").replace(".git", "")
        elif url.startswith("https://github.com/"):
            repo = url.replace("https://github.com/", "").replace(".git", "")
    return repo


@pytest.fixture(scope="module")
def aws_region():
    return get_aws_region()


@pytest.fixture(scope="module")
def aws_account_id():
    return get_aws_account_id()


@pytest.fixture(scope="module")
def github_repo():
    return get_github_repo()


@pytest.fixture(scope="module")
def project_root():
    return REPO_ROOT


@pytest.fixture(scope="module")
def post_dir():
    return POST_DIR


@pytest.fixture(scope="module")
def config_path():
    return CONFIG_PATH
