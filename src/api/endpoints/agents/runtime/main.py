"""
Agent Runtime - Loads prompts from S3 and runs agents with full safety layer.

This runtime supports multiple agents, each defined by a prompt file in S3.
The agent_type is passed in the payload to select which prompt to load.

Architecture:
- Prompts stored in S3 (no redeploy needed for new agents)
- Guardrails for content safety and compliance
- Memory for context persistence across sessions
- Cedar policies for deterministic access control

Note: bedrock_agentcore and strands are AgentCore runtime dependencies.
Type stubs (.pyi files) are provided for mypy type checking.
"""

import json
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

# AgentCore runtime imports - available in AgentCore environment
try:
    from bedrock_agentcore import BedrockAgentCoreApp
    from strands import Agent
    from strands.models import BedrockModel
    _RUNTIME_AVAILABLE = True
except ImportError:
    _RUNTIME_AVAILABLE = False

from tools import ALL_TOOLS

# Initialize the AgentCore app
app = BedrockAgentCoreApp() if _RUNTIME_AVAILABLE else None

# Environment configuration
PROMPTS_BUCKET = os.environ.get("PROMPTS_BUCKET", "")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
MEMORY_ARN = os.environ.get("MEMORY_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")

# Model configuration - Claude Opus 4.5 for maximum capability
MODEL_ID = "us.anthropic.claude-opus-4-5-20251101-v1:0"

# S3 client for fetching prompts
s3_client = boto3.client("s3", region_name=AWS_REGION)


def load_prompt_from_s3(agent_type: str) -> str:
    """Load a prompt file from S3 by agent type."""
    if not PROMPTS_BUCKET:
        raise ValueError("PROMPTS_BUCKET environment variable not set")

    key = f"prompts/{agent_type}.md"

    try:
        response = s3_client.get_object(Bucket=PROMPTS_BUCKET, Key=key)
        return response["Body"].read().decode("utf-8")
    except ClientError as err:
        if err.response["Error"]["Code"] == "NoSuchKey":
            # List available prompts for error message
            try:
                list_response = s3_client.list_objects_v2(
                    Bucket=PROMPTS_BUCKET, Prefix="prompts/", Delimiter="/"
                )
                available = [
                    obj["Key"].replace("prompts/", "").replace(".md", "")
                    for obj in list_response.get("Contents", [])
                    if obj["Key"].endswith(".md")
                ]
                raise ValueError(
                    f"Unknown agent_type: {agent_type}. "
                    f"Available agents: {', '.join(available)}"
                ) from err
            except ClientError:
                raise ValueError(f"Unknown agent_type: {agent_type}") from err
        raise


def extract_recommendation(result: str) -> dict[str, Any]:
    """
    Extract recommendation from agent result.

    Agents can include recommendations in their response by including
    a JSON block with "recommendation" key:

    ```json
    {
        "recommendation": "create_agent",
        "create_agent_request": "Create an agent that..."
    }
    ```
    """
    recommendation = {}

    # Look for JSON blocks in the result
    if "```json" in result:
        try:
            json_start = result.index("```json") + 7
            json_end = result.index("```", json_start)
            json_str = result[json_start:json_end].strip()
            parsed = json.loads(json_str)

            if isinstance(parsed, dict) and "recommendation" in parsed:
                recommendation = parsed
        except (ValueError, json.JSONDecodeError):
            pass

    return recommendation


def _apply_entrypoint(func: Any) -> Any:
    """Apply app.entrypoint if runtime is available."""
    if app is not None:
        return app.entrypoint(func)
    return func


@_apply_entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Main entrypoint for the agent runtime.

    Expected payload:
    {
        "agent_type": "troubleshooter_of_workflows",
        "github_token": "...",
        "session_id": "...",  # Optional - for memory persistence
        ... (agent-specific parameters)
    }
    """
    agent_type = payload.get("agent_type")
    session_id = payload.get("session_id")

    if not agent_type:
        return {"error": "Missing agent_type in payload"}

    try:
        system_prompt = load_prompt_from_s3(agent_type)
    except ValueError as err:
        return {"error": str(err)}

    # Build agent configuration with Claude Opus 4.5
    model = BedrockModel(model_id=MODEL_ID) if _RUNTIME_AVAILABLE else None
    agent_config: dict[str, Any] = {
        "model": model,
        "system_prompt": system_prompt,
        "tools": ALL_TOOLS,
    }

    # Add guardrails if configured
    if GUARDRAIL_ID:
        agent_config["guardrail_configuration"] = {
            "guardrail_id": GUARDRAIL_ID,
            "guardrail_version": GUARDRAIL_VERSION,
        }

    # Add memory if configured
    if MEMORY_ARN and session_id:
        agent_config["memory_configuration"] = {
            "memory_arn": MEMORY_ARN,
            "session_id": session_id,
        }

    # Create agent with the loaded prompt and safety configuration
    agent = Agent(**agent_config)

    # Build the request message from payload
    # Remove agent_type and session_id from payload before passing to agent
    agent_payload = {
        k: v for k, v in payload.items()
        if k not in ("agent_type", "session_id")
    }

    # Format the request based on what's in the payload
    if "run_id" in agent_payload:
        # Workflow troubleshooting request
        request = f"""Analyze and fix this failed workflow:

Repository: {agent_payload.get('owner')}/{agent_payload.get('repo')}
Workflow: {agent_payload.get('workflow_name')}
Workflow Path: {agent_payload.get('workflow_path')}
Run ID: {agent_payload.get('run_id')}
Branch: {agent_payload.get('head_branch')}
Commit SHA: {agent_payload.get('head_sha')}

The github_token for all tool calls is: {agent_payload.get('github_token')}
"""
    elif "request" in agent_payload:
        # Direct request (e.g., for creator_of_agents)
        request = f"""{agent_payload.get('request')}

The github_token for all tool calls is: {agent_payload.get('github_token')}
"""
    else:
        # Generic request - pass payload as context
        request = f"""Process this request:

{json.dumps(agent_payload, indent=2)}
"""

    # Run the agent
    result = agent(request)
    result_message = result.message

    # Extract any recommendations from the result
    recommendation = extract_recommendation(result_message)

    response = {
        "result": result_message,
        "agent_type": agent_type,
        "success": True,
    }

    if recommendation:
        response.update(recommendation)

    return response


if __name__ == "__main__":
    if app is not None:
        app.run()
