"""Helper functions for runners/ecs/images endpoint tests."""
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from repo_utils import REPO_ROOT
from terraform_config import get_shared_config

ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images"
POST_DIR = ENDPOINT_SRC / "post"


def get_aws_region() -> str:
    """Get the AWS region from environment or terraform config."""
    try:
        return os.environ["AWS_REGION"]
    except KeyError:
        return get_shared_config()["aws_region"]


def get_github_repo() -> str:
    """Get the GitHub repository name from terraform config."""
    config = get_shared_config()
    return f"{config['github_org']}/{config['name_for_github_repo']}"


def get_api_fqdn() -> str:
    """Get the API fully qualified domain name."""
    config = get_shared_config()
    return f"api.{config['domain_name']}"


def get_ecr_repository() -> str:
    """Get the ECR repository name for ECS runners."""
    return get_shared_config()["ecr_repository_name_runners"]


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
