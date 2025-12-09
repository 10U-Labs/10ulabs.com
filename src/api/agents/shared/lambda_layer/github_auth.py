"""
Shared GitHub App authentication module for Lambda functions.

This module is included in the github_auth Lambda Layer and provides
GitHub App token generation for all agent Lambdas.

Usage:
    from github_auth import get_github_token

    token = get_github_token()  # Returns a valid installation token
"""

import json
import os
import time
import urllib.request
from typing import Any

import boto3
import jwt

# Cache for installation token (valid for ~1 hour)
_token_cache: dict[str, Any] = {"token": None, "expires_at": 0}

# Default SSM parameter paths
DEFAULT_SSM_APP_ID = "/github/app/id"
DEFAULT_SSM_INSTALLATION_ID = "/github/app/installation_id"
DEFAULT_SSM_PRIVATE_KEY = "/github/app/private_key"


def _get_ssm_parameter(name: str) -> str:
    """Retrieve a parameter from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2"))
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


def _generate_jwt(app_id: str, private_key: str) -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued 60 seconds ago to account for clock drift
        "exp": now + 600,  # Expires in 10 minutes
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def _get_installation_token(app_id: str, installation_id: str, private_key: str) -> str:
    """Get a GitHub App installation access token."""
    app_jwt = _generate_jwt(app_id, private_key)

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "10ULabsBot/1.0",
    }

    req = urllib.request.Request(url, data=b"", headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data["token"]


def get_github_token() -> str:
    """
    Get a GitHub App installation token.

    Returns a cached token if still valid, otherwise generates a new one.
    Tokens are cached for 55 minutes (they're valid for 1 hour).

    Environment variables:
        SSM_GITHUB_APP_ID: SSM parameter name for GitHub App ID
        SSM_GITHUB_APP_INSTALL_ID: SSM parameter name for installation ID
        SSM_GITHUB_APP_PRIVATE_KEY: SSM parameter name for private key
        AWS_REGION_NAME: AWS region for SSM (default: us-east-2)

    Returns:
        str: GitHub installation access token
    """
    now = time.time()

    # Return cached token if still valid (with 5 min buffer)
    if _token_cache["token"] and _token_cache["expires_at"] > now + 300:
        return _token_cache["token"]

    # Get GitHub App credentials from SSM
    app_id = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_ID", DEFAULT_SSM_APP_ID)
    )
    installation_id = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_INSTALL_ID", DEFAULT_SSM_INSTALLATION_ID)
    )
    private_key = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_PRIVATE_KEY", DEFAULT_SSM_PRIVATE_KEY)
    )

    # Generate new installation token
    token = _get_installation_token(app_id, installation_id, private_key)

    # Cache for 55 minutes (tokens are valid for 1 hour)
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + 3300

    return token
