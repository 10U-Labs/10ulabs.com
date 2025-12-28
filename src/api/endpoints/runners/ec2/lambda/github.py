"""GitHub API operations for EC2 runner management.

Re-exports from shared github_runner_api module, with local SSM-dependent functions.
"""
import logging
import os
from typing import Dict

from botocore.exceptions import ClientError

from aws_clients import get_ssm_client
from github_runner_api import (
    get_runner_registration_token,
    list_repo_runners,
    delete_runner,
    cleanup_offline_runners,
    get_existing_runner_for_workflow,
    build_runner_labels,
)

logger = logging.getLogger()

_github_token_cache: Dict[str, str] = {'value': ''}


def reset_github_token_cache():
    """Clear the GitHub token cache for testing purposes."""
    _github_token_cache['value'] = ''


def get_github_token() -> str:
    """Get the GitHub token from SSM Parameter Store, with caching."""
    if _github_token_cache['value']:
        return _github_token_cache['value']

    parameter_name = os.environ['GITHUB_TOKEN_SECRET_NAME']
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        token = response['Parameter']['Value']
        _github_token_cache['value'] = token
        return token
    except (ClientError, ValueError, KeyError) as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


__all__ = [
    'get_github_token',
    'get_runner_registration_token',
    'list_repo_runners',
    'delete_runner',
    'cleanup_offline_runners',
    'get_existing_runner_for_workflow',
    'build_runner_labels',
    'reset_github_token_cache',
]
