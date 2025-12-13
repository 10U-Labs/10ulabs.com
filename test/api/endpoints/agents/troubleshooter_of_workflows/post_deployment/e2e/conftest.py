"""Pytest fixtures for troubleshooter_of_workflows agent e2e tests.

E2E tests verify the full request/response cycle through deployed components:
- HTTP requests to Lambda function URLs
- AgentCore agent invocations

Fixtures are inherited from the integration conftest.py.
"""

# Import all fixtures from integration conftest for e2e tests
from test.api.endpoints.agents.troubleshooter_of_workflows.post_deployment.integration.conftest import (
    agentcore_control_client,
    agentcore_data_client,
    agent_runtime_arn,
    agent_runtime_name,
    ecr_repo_name,
    lambda_client,
    lambda_function_name,
    webhook_url,
    AGENT_RUNTIME_NAME,
    LAMBDA_NAME,
)

__all__ = [
    "agentcore_control_client",
    "agentcore_data_client",
    "agent_runtime_arn",
    "agent_runtime_name",
    "ecr_repo_name",
    "lambda_client",
    "lambda_function_name",
    "webhook_url",
    "AGENT_RUNTIME_NAME",
    "LAMBDA_NAME",
]
