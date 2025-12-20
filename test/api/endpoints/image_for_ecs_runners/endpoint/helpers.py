"""Helper functions for image_for_ecs_runners endpoint tests."""
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional
from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners"
POST_DIR = ENDPOINT_SRC / "post"
SHARED_MODULE_PATH = REPO_ROOT / "lib" / "terraform" / "modules" / "shared" / "outputs.tf"


def _get_terraform_output_value(output_name: str) -> str:
    """Extract a value from terraform outputs.tf file."""
    with open(SHARED_MODULE_PATH, 'r', encoding='utf-8') as f:
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


def get_ecr_repository() -> str:
    """Get the ECR repository name for ECS runners."""
    return _get_terraform_output_value("ecr_repository_name_runners")


@dataclass
class ApiRequestConfig:
    """Configuration for API requests."""

    fqdn: str
    api_key: str
    test_mode_default: bool = True


@dataclass
class ApiRequestParams:
    """Parameters for an API request."""

    path: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    test_mode: Optional[bool] = None


def make_api_request(config: ApiRequestConfig, params: ApiRequestParams) -> dict:
    """Make an API request and return the response.

    Args:
        config: ApiRequestConfig with fqdn and api_key
        params: ApiRequestParams with path, method, headers, body, test_mode

    Returns:
        dict with 'status_code', 'headers', and 'body' keys
    """
    test_mode = params.test_mode if params.test_mode is not None else config.test_mode_default

    url = f"https://{config.fqdn}{params.path}"

    request_headers = {
        "Content-Type": "application/json"
    }
    if test_mode:
        request_headers["x-test-mode"] = "true"
    if config.api_key:
        request_headers["x-api-key"] = config.api_key
    if params.headers:
        request_headers.update(params.headers)

    data = json.dumps(params.body).encode("utf-8") if params.body else None

    req = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=params.method
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return {
                "status_code": response.status,
                "headers": dict(response.headers),
                "body": json.loads(response_body) if response_body else {}
            }
    except urllib.error.HTTPError as e:
        response_body = e.read().decode("utf-8") if e.fp else ""
        return {
            "status_code": e.code,
            "headers": dict(e.headers) if e.headers else {},
            "body": json.loads(response_body) if response_body else {}
        }
