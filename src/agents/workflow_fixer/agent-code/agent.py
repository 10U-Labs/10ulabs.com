"""
Workflow Fixer Agent - AgentCore Runtime

Analyzes GitHub Actions workflow failures and generates fixes.
"""

import json
import base64
import urllib.request
import urllib.error
from typing import Any
from dataclasses import dataclass

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

app = BedrockAgentCoreApp()


def _get_github_headers(token: str) -> dict[str, str]:
    """Get headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "WorkflowFixerAgent/1.0",
    }


def _github_api_request(
    endpoint: str, token: str, method: str = "GET", data: dict | None = None
) -> dict[str, Any]:
    """Make a request to the GitHub API."""
    url = f"https://api.github.com{endpoint}"
    headers = _get_github_headers(token)

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def _github_api_request_raw(endpoint: str, token: str) -> str:
    """Make a request to GitHub API and return raw text response."""
    url = f"https://api.github.com{endpoint}"
    headers = _get_github_headers(token)

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


@tool
def get_workflow_logs(
    owner: str, repo: str, run_id: int, github_token: str
) -> str:
    """
    Fetch the logs from a failed GitHub Actions workflow run.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        run_id: The workflow run ID
        github_token: GitHub Personal Access Token

    Returns:
        The combined logs from all failed jobs in the workflow run
    """
    jobs_endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    jobs_response = _github_api_request(jobs_endpoint, github_token)

    logs_content = []

    for job in jobs_response.get("jobs", []):
        if job.get("conclusion") == "failure":
            job_id = job["id"]
            job_name = job["name"]
            logs_content.append(f"\n=== JOB: {job_name} (ID: {job_id}) ===\n")

            try:
                logs_endpoint = f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                job_logs = _github_api_request_raw(logs_endpoint, github_token)
                logs_content.append(job_logs)
            except RuntimeError as err:
                logs_content.append(f"Could not fetch logs: {err}")

    return "\n".join(logs_content) if logs_content else "No failed job logs found"


@tool
def get_file_content(
    owner: str, repo: str, path: str, ref: str, github_token: str
) -> str:
    """
    Fetch the content of a file from a GitHub repository.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        path: The path to the file in the repository
        ref: The git ref (branch, tag, or commit SHA)
        github_token: GitHub Personal Access Token

    Returns:
        The content of the file
    """
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_api_request(endpoint, github_token)

    if response.get("encoding") == "base64":
        return base64.b64decode(response["content"]).decode("utf-8")
    return response.get("content", "")


@tool
def list_directory(
    owner: str, repo: str, path: str, ref: str, github_token: str
) -> list[dict[str, str]]:
    """
    List files in a directory of a GitHub repository.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        path: The path to the directory in the repository
        ref: The git ref (branch, tag, or commit SHA)
        github_token: GitHub Personal Access Token

    Returns:
        List of files with their names, paths, and types
    """
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_api_request(endpoint, github_token)

    if isinstance(response, list):
        return [
            {"name": item["name"], "path": item["path"], "type": item["type"]}
            for item in response
        ]
    return []


@tool
def create_branch(
    owner: str, repo: str, branch_name: str, base_sha: str, github_token: str
) -> str:
    """
    Create a new branch in a GitHub repository.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        branch_name: The name for the new branch
        base_sha: The commit SHA to branch from
        github_token: GitHub Personal Access Token

    Returns:
        The name of the created branch
    """
    endpoint = f"/repos/{owner}/{repo}/git/refs"
    data = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
    _github_api_request(endpoint, github_token, method="POST", data=data)
    return branch_name


@dataclass
class CommitFileParams:
    """Parameters for committing a file."""

    owner: str
    repo: str
    branch: str
    file_path: str
    content: str
    message: str
    github_token: str


@tool
def commit_file(
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
    content: str,
    message: str,
    github_token: str,
) -> str:
    """
    Create or update a file in a GitHub repository.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        branch: The branch to commit to
        file_path: The path where the file should be created/updated
        content: The new content for the file
        message: The commit message
        github_token: GitHub Personal Access Token

    Returns:
        The commit SHA
    """
    file_sha = None
    try:
        endpoint = f"/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        existing = _github_api_request(endpoint, github_token)
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

    response = _github_api_request(endpoint, github_token, method="PUT", data=data)
    return response.get("commit", {}).get("sha", "unknown")


@dataclass
class PullRequestParams:
    """Parameters for creating a pull request."""

    owner: str
    repo: str
    head_branch: str
    base_branch: str
    title: str
    body: str
    github_token: str


@tool
def create_pull_request(
    owner: str,
    repo: str,
    head_branch: str,
    base_branch: str,
    title: str,
    body: str,
    github_token: str,
) -> dict[str, Any]:
    """
    Create a pull request in a GitHub repository.

    Args:
        owner: The GitHub organization or user that owns the repository
        repo: The repository name
        head_branch: The branch containing your changes
        base_branch: The branch you want to merge into
        title: The title of the pull request
        body: The body/description of the pull request
        github_token: GitHub Personal Access Token

    Returns:
        The created pull request details including URL
    """
    endpoint = f"/repos/{owner}/{repo}/pulls"
    data = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body,
    }
    return _github_api_request(endpoint, github_token, method="POST", data=data)


# Create the agent with tools
agent = Agent(
    system_prompt="""You are an expert CI/CD engineer specializing in GitHub Actions workflows.

Your task is to analyze workflow failures and create fixes. When given information about a failed workflow:

1. Use get_workflow_logs to fetch the failure logs
2. Analyze the error messages to understand what failed and why
3. Use get_file_content to read relevant files (workflow files, source code, config files)
4. Use list_directory to explore the repository structure if needed
5. Determine the root cause and the fix
6. Create a fix branch using create_branch
7. Commit the fix using commit_file
8. Create a pull request using create_pull_request

Be methodical and thorough. Always read the relevant files before proposing changes.
Only create PRs when you are confident the fix is correct.

When creating PRs, include:
- Clear explanation of what failed
- Root cause analysis
- What the fix does and why it works
- Any caveats or manual verification needed""",
    tools=[
        get_workflow_logs,
        get_file_content,
        list_directory,
        create_branch,
        commit_file,
        create_pull_request,
    ],
)


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Main entrypoint for the Workflow Fixer agent.

    Expected payload:
    {
        "github_token": "...",
        "owner": "org-name",
        "repo": "repo-name",
        "run_id": 12345,
        "workflow_name": "workflow-name",
        "workflow_path": ".github/workflows/...",
        "head_sha": "abc123",
        "head_branch": "main"
    }
    """
    github_token = payload.get("github_token")
    owner = payload.get("owner")
    repo = payload.get("repo")
    run_id = payload.get("run_id")
    workflow_name = payload.get("workflow_name")
    workflow_path = payload.get("workflow_path")
    head_sha = payload.get("head_sha")
    head_branch = payload.get("head_branch")

    if not all([github_token, owner, repo, run_id]):
        return {"error": "Missing required parameters"}

    prompt = f"""A GitHub Actions workflow has failed. Please analyze and fix it.

Repository: {owner}/{repo}
Workflow: {workflow_name}
Workflow Path: {workflow_path}
Run ID: {run_id}
Branch: {head_branch}
Commit SHA: {head_sha}

Please:
1. Fetch the workflow logs using get_workflow_logs(
   owner="{owner}", repo="{repo}", run_id={run_id}, github_token="<the token>"
)
2. Analyze the failure
3. Read relevant files to understand the context
4. Create a fix PR if you can determine a solution

The github_token for all tool calls is: {github_token}
"""

    result = agent(prompt)
    return {"result": result.message, "success": True}


if __name__ == "__main__":
    app.run()
