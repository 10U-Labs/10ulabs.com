"""GitHub API utilities using urllib.request (no external dependencies)."""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {"token": None, "ssm_client": None}


def _get_ssm_client() -> Any:
    """Get or create SSM client (singleton)."""
    if _cache["ssm_client"] is None:
        _cache["ssm_client"] = boto3.client("ssm")
    return _cache["ssm_client"]


def get_github_token() -> str:
    """Retrieve GitHub token from SSM Parameter Store with caching."""
    if _cache["token"]:
        return _cache["token"]

    parameter_name = os.environ.get("GITHUB_TOKEN_SECRET_NAME")
    if not parameter_name:
        return ""

    try:
        response = _get_ssm_client().get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        token = response.get("Parameter", {}).get("Value", "")
        _cache["token"] = token
        return token
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        logger.error(
            "[ERROR] Failed to retrieve GitHub token: %s - %s",
            error_code,
            str(err),
        )
        return ""


def clear_token_cache() -> None:
    """Clear the cached GitHub token."""
    _cache["token"] = None


def github_api_request(
    method: str,
    path: str,
    data: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Make a request to the GitHub API using urllib.request.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        path: API path (e.g., "/repos/owner/repo/actions/runners")
        data: Request body for POST/PUT/PATCH requests
        token: GitHub token (uses cached token if not provided)

    Returns:
        Parsed JSON response

    Raises:
        urllib.error.HTTPError: If the request fails
    """
    if token is None:
        token = get_github_token()

    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TenULabs-Lambda",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            if response_body:
                return json.loads(response_body)
            return {}
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        logger.error(
            "[ERROR] GitHub API request failed: %s %s -> %d: %s",
            method,
            path,
            err.code,
            error_body,
        )
        raise
