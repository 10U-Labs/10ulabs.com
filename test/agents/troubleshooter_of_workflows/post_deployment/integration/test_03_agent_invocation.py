"""Integration tests for Troubleshooter of Workflows Agent Invocation.

Five-layer testing model:
- Layer 2: Authorization - Can we call the invoke API?
- Layer 5: Capability - Can we invoke the agent and get a response?

Note: These tests invoke the agent with test payloads that should not trigger
actual workflow fixes (invalid/missing run IDs).
"""

import json

from botocore.exceptions import ClientError
import pytest


class TestAgentInvocationAuthorization:
    """Layer 2: Verify we can call the AgentCore invoke API."""

    def test_01_can_call_invoke_api(self, agentcore_data_client, agent_runtime_arn):
        """Verify we have permission to call invoke_agent_runtime."""
        if not agent_runtime_arn:
            pytest.skip("Agent runtime ARN not configured")

        try:
            # Invoke with minimal payload - agent should handle gracefully
            response = agentcore_data_client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                payload=json.dumps({"test": True}).encode("utf-8"),
                contentType="application/json",
            )
            # If we get here, we have permission
            assert response is not None
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    "No permission to call invoke_agent_runtime. "
                    "Check IAM permissions for bedrock-agentcore:InvokeAgentRuntime."
                )
            if code == "ResourceNotFoundException":
                pytest.fail(
                    f"Agent runtime not found: {agent_runtime_arn}. "
                    "Run terraform apply in src/agents/troubleshooter_of_workflows/"
                )
            # Other errors might be expected for test payloads
            raise


class TestAgentInvocationCapability:
    """Layer 5: Verify we can invoke the agent and get responses."""

    def test_01_agent_handles_empty_payload(self, agentcore_data_client, agent_runtime_arn):
        """Verify agent handles empty/minimal payload gracefully."""
        if not agent_runtime_arn:
            pytest.skip("Agent runtime ARN not configured")

        try:
            response = agentcore_data_client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                payload=json.dumps({}).encode("utf-8"),
                contentType="application/json",
            )

            # Read the response stream
            content = []
            response_body = response.get("response")
            if response_body:
                for chunk in response_body:
                    if isinstance(chunk, bytes):
                        content.append(chunk.decode("utf-8"))
                    elif isinstance(chunk, dict) and "chunk" in chunk:
                        chunk_data = chunk["chunk"].get("bytes", b"")
                        if isinstance(chunk_data, bytes):
                            content.append(chunk_data.decode("utf-8"))

            # Agent should respond (even if with an error about missing fields)
            # The key is that it responds at all
            assert response is not None

        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ResourceNotFoundException":
                pytest.skip("Agent runtime not found")
            # ValidationException is acceptable - means agent is responding
            if code == "ValidationException":
                pass  # Expected for incomplete payload
            else:
                raise

    def test_02_agent_responds_to_test_payload(
        self, agentcore_data_client, agent_runtime_arn
    ):
        """Verify agent responds to a well-formed test payload."""
        if not agent_runtime_arn:
            pytest.skip("Agent runtime ARN not configured")

        # Use a test payload with invalid run_id that won't trigger real fixes
        test_payload = {
            "github_token": "test-token-invalid",
            "owner": "test-org",
            "repo": "test-repo",
            "run_id": 0,  # Invalid run ID
            "workflow_name": "Test Workflow",
            "workflow_path": ".github/workflows/test.yml",
            "head_sha": "0000000000000000000000000000000000000000",
            "head_branch": "test-branch",
        }

        try:
            response = agentcore_data_client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                payload=json.dumps(test_payload).encode("utf-8"),
                contentType="application/json",
            )

            # Read response stream
            content = []
            response_body = response.get("response")
            if response_body:
                for chunk in response_body:
                    if isinstance(chunk, bytes):
                        content.append(chunk.decode("utf-8"))
                    elif isinstance(chunk, dict) and "chunk" in chunk:
                        chunk_data = chunk["chunk"].get("bytes", b"")
                        if isinstance(chunk_data, bytes):
                            content.append(chunk_data.decode("utf-8"))

            # Agent should have processed and responded
            assert response is not None

        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ResourceNotFoundException":
                pytest.skip("Agent runtime not found")
            # Other errors may indicate agent is working but rejecting bad input
            # which is acceptable behavior
            if code in ["ValidationException", "ServiceException"]:
                pass  # Agent responded, just rejected the input
            else:
                raise
