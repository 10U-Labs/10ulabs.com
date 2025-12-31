"""Pytest fixtures for runners/ec2/images post tests."""
import json
import os
import re
import subprocess
import pytest
from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2" / "images"
POST_DIR = ENDPOINT_SRC / "post"
CONFIG_PATH = POST_DIR / "config.json"
COMMON_MODULE_PATH = REPO_ROOT / "lib" / "terraform" / "common" / "outputs.tf"
TFVARS_PATH = REPO_ROOT / "src" / "api" / "common" / "routing" / "terraform.tfvars"


def _parse_locals() -> dict:
    """Parse locals from shared module locals.tf."""
    locals_path = REPO_ROOT / "lib" / "terraform" / "common" / "locals.tf"
    with open(locals_path, 'r', encoding='utf-8') as f:
        content = f.read()
    values = {}
    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        key, value = match.groups()
        values[key] = value
    return values


def _get_terraform_output_value(output_name: str) -> str:
    """ get terraform output value."""
    with open(COMMON_MODULE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    # Try literal string value first
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    # Try local.* reference
    local_pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*local\.(\w+)'
    local_match = re.search(local_pattern, content)
    if local_match:
        local_name = local_match.group(1)
        locals_dict = _parse_locals()
        return locals_dict.get(local_name, '')
    return ''


def get_aws_region() -> str:
    """Get aws region."""
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_output_value("aws_region")
    return region


def get_aws_account_id() -> str:
    """Get aws account id."""
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_github_repo() -> str:
    """Get github repo."""
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


@pytest.fixture(scope="session")
def aws_region():
    """Aws region."""
    return get_aws_region()


@pytest.fixture(scope="session")
def aws_account_id():
    """Aws account id."""
    return get_aws_account_id()


@pytest.fixture(scope="session")
def github_repo():
    """Github repo."""
    return get_github_repo()


@pytest.fixture(scope="session")
def project_root():
    """Project root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def post_dir():
    """Post dir."""
    return POST_DIR


@pytest.fixture(scope="session")
def config():
    """Config."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        raw_config = json.load(f)
    source_ami = raw_config.get("source_ami", "")
    parts = source_ami.split("-")
    result = {
        **raw_config,
        "os_family": parts[0] if len(parts) > 0 else "",
        "os_version": parts[1] if len(parts) > 1 else "",
        "os_architecture": parts[2] if len(parts) > 2 else "",
        "github_runner_iam_instance_profile_name": "GitHubSelfHostedRunnerInstanceProfile",
        "ec2_max_spot_price": "0.25",
    }
    return result
