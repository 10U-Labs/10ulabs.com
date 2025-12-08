"""
Webhook Lambda - Receives GitHub workflow_run events and invokes AgentCore agent.
"""

import json
import logging
import os
import traceback
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_github_pat() -> str:
    """Retrieve GitHub PAT from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2"))
    param_name = os.environ.get("SSM_GITHUB_PAT", "/TenULabs/github_pat")
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def invoke_agent(payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the AgentCore workflow fixer agent."""
    client = boto3.client(
        "bedrock-agentcore", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2")
    )

    agent_arn = os.environ.get("AGENT_RUNTIME_ARN")
    if not agent_arn:
        raise ValueError("AGENT_RUNTIME_ARN environment variable not set")

    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        payload=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
    )

    content = []
    response_body = response.get("response")
    if response_body:
        for chunk in response_body:
            if isinstance(chunk, bytes):
                content.append(chunk.decode("utf-8"))
            else:
                content.append(str(chunk))

    return json.loads("".join(content)) if content else {}


def _parse_webhook_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Parse the webhook payload from the event."""
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body)
    return body


def _should_skip_event(payload: dict[str, Any]) -> tuple[bool, str]:
    """Check if event should be skipped. Returns (should_skip, reason)."""
    action = payload.get("action")
    workflow_run = payload.get("workflow_run", {})

    if action != "completed":
        return True, "Ignoring non-completed event"

    conclusion = workflow_run.get("conclusion")
    if conclusion != "failure":
        return True, f"Ignoring {conclusion} workflow"

    workflow_name = workflow_run.get("name", "")
    if "workflow-fixer" in workflow_name.lower():
        return True, "Ignoring workflow-fixer workflow"

    return False, ""


def _build_agent_payload(
    payload: dict[str, Any], github_token: str
) -> dict[str, Any]:
    """Build the payload for the AgentCore agent."""
    workflow_run = payload.get("workflow_run", {})
    repo = payload.get("repository", {})

    return {
        "github_token": github_token,
        "owner": repo.get("owner", {}).get("login"),
        "repo": repo.get("name"),
        "run_id": workflow_run.get("id"),
        "workflow_name": workflow_run.get("name"),
        "workflow_path": workflow_run.get("path", ""),
        "head_sha": workflow_run.get("head_sha"),
        "head_branch": workflow_run.get("head_branch"),
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Main Lambda handler for GitHub webhook events."""
    logger.info("Received event: %s", json.dumps(event))

    payload = _parse_webhook_payload(event)
    should_skip, reason = _should_skip_event(payload)

    if should_skip:
        return {"statusCode": 200, "body": json.dumps({"message": reason})}

    workflow_run = payload.get("workflow_run", {})
    repo = payload.get("repository", {})
    logger.info(
        "Processing failed workflow: %s (run %s) in %s/%s",
        workflow_run.get("name"),
        workflow_run.get("id"),
        repo.get("owner", {}).get("login"),
        repo.get("name"),
    )

    try:
        github_token = get_github_pat()
        agent_payload = _build_agent_payload(payload, github_token)
        result = invoke_agent(agent_payload)
        logger.info("Agent result: %s", json.dumps(result, indent=2))

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Agent invoked", "result": result}),
        }

    except (ClientError, ValueError, json.JSONDecodeError) as err:
        logger.error("Error processing workflow failure: %s", err)
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(err)})}
