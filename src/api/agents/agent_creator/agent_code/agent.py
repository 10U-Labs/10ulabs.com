"""
Agent Creator - creates new agents as needed.

Has full access to GitHub and AWS. Figures out how to do its job.
"""

import json
import base64
import urllib.request
import urllib.error
from typing import Any

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

app = BedrockAgentCoreApp()


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AgentCreator/1.0",
    }


def _github_request(
    endpoint: str, token: str, method: str = "GET", data: dict | None = None
) -> dict[str, Any] | list[Any]:
    url = f"https://api.github.com{endpoint}"
    headers = _github_headers(token)
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


@tool
def github_get_file(owner: str, repo: str, path: str, ref: str, token: str) -> str:
    """Get file content from GitHub repository."""
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_request(endpoint, token)
    if isinstance(response, dict) and response.get("encoding") == "base64":
        return base64.b64decode(response["content"]).decode("utf-8")
    return ""


@tool
def github_list_dir(owner: str, repo: str, path: str, ref: str, token: str) -> str:
    """List directory contents in GitHub repository."""
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = _github_request(endpoint, token)
    if isinstance(response, list):
        return json.dumps([{"name": f["name"], "type": f["type"]} for f in response])
    return "[]"


@tool
def github_create_branch(owner: str, repo: str, branch: str, sha: str, token: str) -> str:
    """Create a new branch."""
    endpoint = f"/repos/{owner}/{repo}/git/refs"
    data = {"ref": f"refs/heads/{branch}", "sha": sha}
    _github_request(endpoint, token, method="POST", data=data)
    return branch


@tool
def github_put_file(
    owner: str, repo: str, path: str, content: str, message: str, branch: str, token: str
) -> str:
    """Create or update a file in the repository."""
    # Check if file exists
    sha = None
    try:
        endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        existing = _github_request(endpoint, token)
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except urllib.error.HTTPError:
        pass

    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    response = _github_request(endpoint, token, method="PUT", data=data)
    return response.get("commit", {}).get("sha", "done")


@tool
def github_create_pr(
    owner: str, repo: str, head: str, base: str, title: str, body: str, token: str
) -> str:
    """Create a pull request."""
    endpoint = f"/repos/{owner}/{repo}/pulls"
    data = {"title": title, "head": head, "base": base, "body": body}
    response = _github_request(endpoint, token, method="POST", data=data)
    return response.get("html_url", "")


@tool
def github_get_ref(owner: str, repo: str, ref: str, token: str) -> str:
    """Get the SHA of a git ref (branch/tag)."""
    endpoint = f"/repos/{owner}/{repo}/git/ref/heads/{ref}"
    response = _github_request(endpoint, token)
    return response.get("object", {}).get("sha", "")


@tool
def aws_ssm_get(name: str, region: str) -> str:
    """Get a parameter from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=region)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


@tool
def aws_s3_put(bucket: str, key: str, content: str, region: str) -> str:
    """Put an object in S3."""
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))
    return f"s3://{bucket}/{key}"


@tool
def aws_s3_get(bucket: str, key: str, region: str) -> str:
    """Get an object from S3."""
    s3 = boto3.client("s3", region_name=region)
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


@tool
def aws_lambda_invoke(function_name: str, payload: str, region: str) -> str:
    """Invoke a Lambda function."""
    client = boto3.client("lambda", region_name=region)
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=payload.encode("utf-8"),
    )
    return response["Payload"].read().decode("utf-8")


agent = Agent(
    system_prompt="""You are the Agent Creator. You create new agents.

FIRST: Read docs/tenets/AGENTS.md - these are your non-negotiable rules.

Key tenets (in priority order):
1. LEGAL COMPLIANCE - DO NOT VIOLATE ANY U.S. LAWS. EVER. NOT NEGOTIABLE.
2. PROFITABILITY - actions should contribute to legal profits
3. AFFORDABILITY - keep costs low, be efficient
4. ATOMICITY - each agent does ONE thing well
5. OBSERVABILITY - all actions must be logged, no rogue agents

You have full access to GitHub and AWS. You figure out how to do your job.

When asked to create an agent:
1. Understand what the agent needs to do
2. Look at existing agents in src/agents/ to understand the patterns
3. Create the necessary files (terraform, code, tests, workflow)
4. Create a PR with your changes

You decide:
- What the agent should look like
- What tools it needs
- How it should be structured
- What permissions it needs

Keep agents atomic - they should do one thing well.

Available tools:
- github_get_file, github_list_dir, github_put_file, github_create_branch, github_create_pr, github_get_ref
- aws_ssm_get, aws_s3_put, aws_s3_get, aws_lambda_invoke

The GitHub PAT is in SSM at /TenULabs/github_pat
The repo is 10U-Labs-LLC/10ulabs.com""",
    tools=[
        github_get_file,
        github_list_dir,
        github_create_branch,
        github_put_file,
        github_create_pr,
        github_get_ref,
        aws_ssm_get,
        aws_s3_put,
        aws_s3_get,
        aws_lambda_invoke,
    ],
)


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Main entrypoint."""
    request = payload.get("request", "")
    if not request:
        return {"error": "No request provided"}

    result = agent(request)
    return {"result": result.message, "success": True}


if __name__ == "__main__":
    app.run()
