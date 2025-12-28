"""GitHub Actions runner API operations."""
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

from aws_clients import get_ssm_client

logger = logging.getLogger()

_github_token_cache: Dict[str, str] = {'value': ''}


def reset_github_token_cache():
    """Clear the GitHub token cache for testing purposes."""
    _github_token_cache['value'] = ''


def get_github_token() -> str:
    """Get the GitHub token from SSM Parameter Store, with caching."""
    if _github_token_cache['value']:
        return _github_token_cache['value']

    parameter_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME', '')
    if not parameter_name:
        logger.error("GITHUB_TOKEN_SECRET_NAME not set")
        return ''
    try:
        from botocore.exceptions import ClientError
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        token = response['Parameter']['Value']
        _github_token_cache['value'] = token
        return token
    except Exception as e:  # Catch ClientError and other exceptions
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


def get_runner_registration_token(github_token: str, github_repo: str) -> str:
    """Get a new runner registration token from the GitHub API."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{github_repo}/actions/runners/registration-token',
        method='POST',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data.get('token', '')
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        logger.error("Failed to get runner registration token: %s", e)
        return ''


def list_repo_runners(github_token: str, github_repo: str) -> List[Dict[str, Any]]:
    """List all runners registered for a GitHub repository."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    runners: List[Dict[str, Any]] = []
    page = 1
    while True:
        req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners?per_page=100&page={page}',
            headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                page_runners = data.get('runners', [])
                runners.extend(page_runners)
                if len(page_runners) < 100:
                    break
                page += 1
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            logger.error("Failed to list runners: %s", e)
            break
    return runners


def delete_runner(github_token: str, github_repo: str, runner_id: int) -> bool:
    """Delete a runner from a GitHub repository."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{github_repo}/actions/runners/{runner_id}',
        method='DELETE',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            success = response.status == 204
            if success:
                logger.info("Deleted runner %s", runner_id)
            return success
    except urllib.error.HTTPError as e:
        if e.code == 204:
            logger.info("Deleted runner %s", runner_id)
            return True
        logger.error("Failed to delete runner %s: %s", runner_id, e)
        return False
    except (urllib.error.URLError, ValueError) as e:
        logger.error("Failed to delete runner %s: %s", runner_id, e)
        return False


def cleanup_offline_runners(
        github_token: str, github_repo: str, run_id: int | None) -> Dict[str, Any]:
    """Clean up offline runners for a specific workflow run."""
    runners = list_repo_runners(github_token, github_repo)
    run_id_label = f'runner-{run_id}' if run_id else None
    offline_runners = []
    for runner in runners:
        if runner.get('status') != 'offline':
            continue
        if not run_id_label:
            continue
        runner_labels = {label.get('name') for label in runner.get('labels', [])}
        if run_id_label not in runner_labels:
            continue
        offline_runners.append(runner)
    deleted_count = 0
    failed_count = 0
    for runner in offline_runners:
        runner_id = runner.get('id')
        runner_name = runner.get('name')
        if runner_id is None:
            continue
        logger.info("Removing offline runner: %s (id=%s)", runner_name, runner_id)
        if delete_runner(github_token, github_repo, int(runner_id)):
            deleted_count += 1
        else:
            failed_count += 1
    result = {
        'found': len(offline_runners),
        'deleted': deleted_count,
        'failed': failed_count
    }
    if deleted_count > 0:
        logger.info("Cleaned up %d offline runners for run_id %s", deleted_count, run_id)
    return result


def get_existing_runner_for_workflow(
        github_token: str, github_repo: str,
        run_id: int, job_labels: list) -> Dict[str, Any] | None:
    """Find an existing runner that can handle a workflow job."""
    result = None
    runners = list_repo_runners(github_token, github_repo)
    runner_label = f'runner-{run_id}'
    required_labels = set(job_labels)
    for runner in runners:
        runner_labels = {label.get('name') for label in runner.get('labels', [])}
        has_run_id_label = runner_label in runner_labels
        has_required_labels = required_labels.issubset(runner_labels)
        is_available = runner.get('status') in ('online', 'busy')
        if has_run_id_label and has_required_labels and is_available:
            result = runner
    return result


def build_runner_labels(job_labels: List[str], run_id: int | None) -> List[str]:
    """Build the complete list of labels for a GitHub runner."""
    base_labels = ['self-hosted', 'linux', 'x64']
    for label in job_labels:
        if label not in base_labels:
            base_labels.append(label)
    if run_id:
        base_labels.append(f'runner-{run_id}')
    return base_labels
