"""
Shared tools for all agents.

All agents have access to the same tools. The prompt controls
which tools each agent actually uses.

Note: strands is a container-only dependency.
Type stubs (.pyi files) are provided for mypy type checking.
"""

import json
import base64
import ssl
import time
import urllib.request
import urllib.error
from typing import Any, Callable, TypeVar

import boto3
import certifi

# Container-only import - stub provided for type checking
try:
    from strands import tool
except ImportError:
    T = TypeVar("T", bound=Callable[..., Any])

    def tool(func: T) -> T:
        """No-op decorator when strands is not available."""
        return func


# =============================================================================
# GitHub API Tools
# =============================================================================

# Retry configuration
_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


def _create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with certifi CA bundle for container environments."""
    return ssl.create_default_context(cafile=certifi.where())


def _github_headers(token: str) -> dict[str, str]:
    """Get headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "10ULabsAgent/1.0",
    }


def _github_request(
    endpoint: str,
    token: str,
    method: str = "GET",
    data: dict | None = None,
) -> Any:
    """Make a request to the GitHub API with retry logic."""
    url = f"https://api.github.com{endpoint}"
    headers = _github_headers(token)
    body = json.dumps(data).encode("utf-8") if data else None
    ssl_context = _create_ssl_context()

    for attempt in range(_MAX_RETRIES + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(
                req, timeout=30, context=ssl_context
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            error_body = err.read().decode("utf-8") if err.fp else ""
            if err.code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES:
                time.sleep(_BASE_DELAY * (2**attempt))
                continue
            raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err

    raise RuntimeError("Unexpected error in _github_request")


def _github_request_raw(endpoint: str, token: str) -> str:
    """Make a request to GitHub API and return raw text response with retry logic."""
    url = f"https://api.github.com{endpoint}"
    headers = _github_headers(token)
    ssl_context = _create_ssl_context()

    for attempt in range(_MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(
                req, timeout=60, context=ssl_context
            ) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            error_body = err.read().decode("utf-8") if err.fp else ""
            if err.code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES:
                time.sleep(_BASE_DELAY * (2**attempt))
                continue
            raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err

    raise RuntimeError("Unexpected error in _github_request_raw")


@tool
def get_workflow_logs(
    owner: str, repo: str, run_id: int, github_token: str
) -> str:
    """
    Fetch logs from a GitHub Actions workflow run.

    Args:
        owner: GitHub org/user that owns the repository
        repo: Repository name
        run_id: Workflow run ID
        github_token: GitHub token

    Returns:
        Combined logs from all failed jobs
    """
    jobs_endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    jobs_response = _github_request(jobs_endpoint, github_token)

    logs_content = []

    for job in jobs_response.get("jobs", []):
        if job.get("conclusion") == "failure":
            job_id = job["id"]
            job_name = job["name"]
            logs_content.append(f"\n=== JOB: {job_name} (ID: {job_id}) ===\n")

            try:
                logs_endpoint = f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                job_logs = _github_request_raw(logs_endpoint, github_token)
                logs_content.append(job_logs)
            except RuntimeError as err:
                logs_content.append(f"Could not fetch logs: {err}")

    return "\n".join(logs_content) if logs_content else "No failed job logs found"


@tool
def get_file_content(
    owner: str, repo: str, path: str, ref: str, github_token: str
) -> str:
    """
    Fetch file content from a GitHub repository.

    Args:
        owner: GitHub org/user that owns the repository
        repo: Repository name
        path: Path to file in repository
        ref: Git ref (branch, tag, or commit SHA)
        github_token: GitHub token

    Returns:
        File content
    """
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_request(endpoint, github_token)

    if isinstance(response, dict) and response.get("encoding") == "base64":
        return base64.b64decode(response["content"]).decode("utf-8")
    return response.get("content", "") if isinstance(response, dict) else ""


@tool
def list_directory(
    owner: str, repo: str, path: str, ref: str, github_token: str
) -> str:
    """
    List files in a directory of a GitHub repository.

    Args:
        owner: GitHub org/user that owns the repository
        repo: Repository name
        path: Path to directory in repository
        ref: Git ref (branch, tag, or commit SHA)
        github_token: GitHub token

    Returns:
        JSON string of files with name, path, and type
    """
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_request(endpoint, github_token)

    if isinstance(response, list):
        files = [
            {"name": item["name"], "path": item["path"], "type": item["type"]}
            for item in response
        ]
        return json.dumps(files, indent=2)
    return "[]"


@tool
def get_ref_sha(owner: str, repo: str, ref: str, github_token: str) -> str:
    """
    Get the SHA of a git ref (branch/tag).

    Args:
        owner: GitHub org/user that owns the repository
        repo: Repository name
        ref: Branch or tag name
        github_token: GitHub token

    Returns:
        Commit SHA
    """
    endpoint = f"/repos/{owner}/{repo}/git/ref/heads/{ref}"
    response = _github_request(endpoint, github_token)
    return response.get("object", {}).get("sha", "")


@tool
def create_branch(
    owner: str, repo: str, branch_name: str, base_sha: str, github_token: str
) -> str:
    """
    Create a new branch in a GitHub repository.

    Args:
        owner: GitHub org/user that owns the repository
        repo: Repository name
        branch_name: Name for the new branch
        base_sha: Commit SHA to branch from
        github_token: GitHub token

    Returns:
        Name of created branch
    """
    endpoint = f"/repos/{owner}/{repo}/git/refs"
    data = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
    _github_request(endpoint, github_token, method="POST", data=data)
    return branch_name


@tool
def commit_file(
    repo_path: str,
    branch_and_file: str,
    content: str,
    message: str,
    github_token: str,
) -> str:
    """
    Create or update a file in a GitHub repository.

    Args:
        repo_path: Repository in "owner/repo" format
        branch_and_file: Branch and file path in "branch:path/to/file" format
        content: New content for the file
        message: Commit message
        github_token: GitHub token

    Returns:
        Commit SHA
    """
    owner, repo = repo_path.split("/", 1)
    branch, file_path = branch_and_file.split(":", 1)

    # Check if file exists to get its SHA
    file_sha = None
    try:
        endpoint = f"/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        existing = _github_request(endpoint, github_token)
        if isinstance(existing, dict):
            file_sha = existing.get("sha")
    except RuntimeError:
        pass

    endpoint = f"/repos/{owner}/{repo}/contents/{file_path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if file_sha:
        data["sha"] = file_sha

    response = _github_request(endpoint, github_token, method="PUT", data=data)
    return response.get("commit", {}).get("sha", "unknown")


@tool
def create_pull_request(
    repo_path: str,
    branches: str,
    title: str,
    body: str,
    github_token: str,
) -> str:
    """
    Create a pull request in a GitHub repository.

    Args:
        repo_path: Repository in "owner/repo" format
        branches: Branches in "head...base" format (e.g., "feature...main")
        title: PR title
        body: PR description
        github_token: GitHub token

    Returns:
        PR URL
    """
    owner, repo = repo_path.split("/", 1)
    head_branch, base_branch = branches.split("...", 1)

    endpoint = f"/repos/{owner}/{repo}/pulls"
    data = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body,
    }
    response = _github_request(endpoint, github_token, method="POST", data=data)
    return response.get("html_url", "")


# =============================================================================
# AWS Tools
# =============================================================================

@tool
def aws_ssm_get(name: str, region: str) -> str:
    """
    Get a parameter from SSM Parameter Store.

    Args:
        name: Parameter name
        region: AWS region

    Returns:
        Parameter value
    """
    ssm = boto3.client("ssm", region_name=region)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


@tool
def aws_s3_put(bucket: str, key: str, content: str, region: str) -> str:
    """
    Put an object in S3.

    Args:
        bucket: S3 bucket name
        key: Object key
        content: Content to store
        region: AWS region

    Returns:
        S3 URI
    """
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))
    return f"s3://{bucket}/{key}"


@tool
def aws_s3_get(bucket: str, key: str, region: str) -> str:
    """
    Get an object from S3.

    Args:
        bucket: S3 bucket name
        key: Object key
        region: AWS region

    Returns:
        Object content
    """
    s3 = boto3.client("s3", region_name=region)
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


@tool
def aws_lambda_invoke(function_name: str, payload: str, region: str) -> str:
    """
    Invoke a Lambda function.

    Args:
        function_name: Lambda function name or ARN
        payload: JSON payload
        region: AWS region

    Returns:
        Lambda response payload
    """
    client = boto3.client("lambda", region_name=region)
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=payload.encode("utf-8"),
    )
    return response["Payload"].read().decode("utf-8")


# =============================================================================
# All tools list
# =============================================================================

ALL_TOOLS = [
    # GitHub tools
    get_workflow_logs,
    get_file_content,
    list_directory,
    get_ref_sha,
    create_branch,
    commit_file,
    create_pull_request,
    # AWS tools
    aws_ssm_get,
    aws_s3_put,
    aws_s3_get,
    aws_lambda_invoke,
]
