import os
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
POST_DIR = ENDPOINT_SRC / "post"
SHARED_MODULE_PATH = REPO_ROOT / "lib" / "terraform" / "outputs.tf"


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


def get_github_repo() -> str:
    return _get_terraform_output_value("github_org") + "/" + _get_terraform_output_value("name_for_github_repo")


def get_api_fqdn() -> str:
    domain_name = _get_terraform_output_value("domain_name")
    return f"api.{domain_name}"
