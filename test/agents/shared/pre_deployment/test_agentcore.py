"""Pre-deployment tests for agents/shared AgentCore Terraform configuration."""
import re


def test_agentcore_tf_defines_execution_role(agents_shared_dir):
    """Test that agentcore.tf defines the execution role."""
    agentcore_tf = agents_shared_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    pattern = r'resource\s+"aws_iam_role"\s+"agentcore_execution"'
    assert re.search(pattern, content) is not None


def test_agentcore_execution_role_has_bedrock_service_principal(agents_shared_dir):
    """Test that execution role allows Bedrock AgentCore to assume it."""
    agentcore_tf = agents_shared_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "bedrock-agentcore.amazonaws.com" in content


def test_agentcore_has_managed_policy_attachment(agents_shared_dir):
    """Test that BedrockAgentCoreFullAccess managed policy is attached."""
    agentcore_tf = agents_shared_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "BedrockAgentCoreFullAccess" in content
