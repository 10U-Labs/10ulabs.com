"""Helper functions for runners/ec2/images endpoint tests."""
import os
import re
from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2" / "images"
POST_DIR = ENDPOINT_SRC / "post"
COMMON_MODULE_PATH = REPO_ROOT / "lib" / "terraform" / "common" / "outputs.tf"


def _get_terraform_output_value(output_name: str) -> str:
    """Extract a value from terraform outputs.tf file."""
    with open(COMMON_MODULE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    result = match.group(1) if match else ''
    return result


def get_aws_region() -> str:
    """Get the AWS region from environment or terraform outputs."""
    try:
        region = os.environ["AWS_REGION"]
    except KeyError:
        region = _get_terraform_output_value("aws_region")
    return region


def get_github_repo() -> str:
    """Get the GitHub repository name from terraform outputs."""
    org = _get_terraform_output_value("github_org")
    repo = _get_terraform_output_value("name_for_github_repo")
    return f"{org}/{repo}"


def get_api_fqdn() -> str:
    """Get the API fully qualified domain name."""
    domain_name = _get_terraform_output_value("domain_name")
    return f"api.{domain_name}"
