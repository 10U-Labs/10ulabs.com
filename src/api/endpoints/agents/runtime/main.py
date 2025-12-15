"""
Agent Runtime - Loads prompts dynamically and runs agents.

This runtime supports multiple agents, each defined by a prompt file
in the prompts/ directory. The agent_type is passed in the payload
to select which prompt to load.

Note: bedrock_agentcore and strands are container-only dependencies.
Type stubs (.pyi files) are provided for mypy type checking.
"""

import json
from pathlib import Path
from typing import Any

# Container-only imports - stubs provided for type checking
try:
    from bedrock_agentcore import BedrockAgentCoreApp
    from strands import Agent
    _RUNTIME_AVAILABLE = True
except ImportError:
    _RUNTIME_AVAILABLE = False

from tools import ALL_TOOLS

app = BedrockAgentCoreApp() if _RUNTIME_AVAILABLE else None

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(agent_type: str) -> str:
    """Load a prompt file by agent type."""
    prompt_path = PROMPTS_DIR / f"{agent_type}.md"

    if not prompt_path.exists():
        available = [p.stem for p in PROMPTS_DIR.glob("*.md")]
        raise ValueError(
            f"Unknown agent_type: {agent_type}. "
            f"Available agents: {', '.join(available)}"
        )

    return prompt_path.read_text(encoding="utf-8")


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
        ... (agent-specific parameters)
    }
    """
    agent_type = payload.get("agent_type")

    if not agent_type:
        return {"error": "Missing agent_type in payload"}

    try:
        system_prompt = load_prompt(agent_type)
    except ValueError as err:
        return {"error": str(err)}

    # Create agent with the loaded prompt
    agent = Agent(
        system_prompt=system_prompt,
        tools=ALL_TOOLS,
    )

    # Build the request message from payload
    # Remove agent_type from payload before passing to agent
    agent_payload = {k: v for k, v in payload.items() if k != "agent_type"}

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
