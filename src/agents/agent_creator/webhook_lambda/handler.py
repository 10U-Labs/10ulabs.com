"""
Invocation Lambda for Agent Creator.
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
    """Invoke the AgentCore agent."""
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


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Main Lambda handler."""
    logger.info("Received event: %s", json.dumps(event))

    try:
        # Parse request from body or direct invocation
        if "body" in event:
            body = event.get("body", "{}")
            if isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
        else:
            payload = event

        request = payload.get("request", "")
        if not request:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No request provided"}),
            }

        result = invoke_agent({"request": request})
        logger.info("Agent result: %s", json.dumps(result, indent=2))

        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}),
        }

    except (ClientError, ValueError, json.JSONDecodeError) as err:
        logger.error("Error: %s", err)
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(err)})}
