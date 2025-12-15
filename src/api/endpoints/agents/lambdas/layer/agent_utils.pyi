"""Type stubs for agent_utils module."""

from typing import Any, Callable

def invoke_agent(agent_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...
def handle_recommendation(result: dict[str, Any], github_token: str) -> dict[str, Any]: ...
def process_sqs_records(
    event: dict[str, Any],
    github_token: str,
    processor: Callable[[dict[str, Any], str], dict[str, Any]],
) -> dict[str, Any]: ...
