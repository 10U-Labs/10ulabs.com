"""
Shared utilities for agent Lambda handlers.

This module provides common functionality used across webhook, scanner, and invoker
Lambda handlers.
"""

import json
import logging
import os
import traceback
from typing import Any, Callable

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()


def invoke_agent(agent_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the AgentCore runtime with a specific agent type."""
    client = boto3.client(
        "bedrock-agentcore", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2")
    )

    agent_arn = os.environ.get("AGENT_RUNTIME_ARN")
    if not agent_arn:
        raise ValueError("AGENT_RUNTIME_ARN environment variable not set")

    payload["agent_type"] = agent_type

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


def handle_recommendation(result: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Handle agent recommendations by routing to appropriate agents."""
    recommendation = result.get("recommendation")

    if recommendation == "create_agent":
        create_request = result.get("create_agent_request", {})
        if isinstance(create_request, str):
            create_request = {"request": create_request}

        create_request["github_token"] = github_token
        logger.info("Routing to creator_of_agents: %s", create_request.get("request", "")[:100])

        creator_result = invoke_agent("creator_of_agents", create_request)
        return {
            "original_result": result,
            "creator_result": creator_result,
            "routed_to": "creator_of_agents",
        }

    return result


def process_sqs_records(
    event: dict[str, Any],
    github_token: str,
    processor: Callable[[dict[str, Any], str], dict[str, Any]],
) -> dict[str, Any]:
    """
    Process SQS records with a given processor function.

    Args:
        event: SQS event with Records
        github_token: GitHub token for API calls
        processor: Function that takes (body, github_token) and returns result dict

    Returns:
        Lambda response with batchItemFailures for partial failures
    """
    logger.info("Received SQS event with %d records", len(event.get("Records", [])))

    results = []
    failed_message_ids = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record.get("body", "{}"))
            result = processor(body, github_token)
            results.append({"messageId": message_id, **result})

        except (ClientError, ValueError, json.JSONDecodeError, RuntimeError) as err:
            logger.error("Error processing message %s: %s", message_id, err)
            traceback.print_exc()
            failed_message_ids.append(message_id)
            results.append({"messageId": message_id, "status": "error", "error": str(err)})

    response: dict[str, Any] = {
        "statusCode": 200,
        "body": json.dumps({"processed": len(results), "results": results}),
    }

    if failed_message_ids:
        response["batchItemFailures"] = [
            {"itemIdentifier": msg_id} for msg_id in failed_message_ids
        ]

    return response
