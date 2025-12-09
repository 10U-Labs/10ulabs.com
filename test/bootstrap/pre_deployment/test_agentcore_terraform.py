"""Pre-deployment tests for AgentCore Terraform configuration."""
import re


def test_agentcore_tf_file_exists(bootstrap_dir):
    """Test that agentcore.tf file exists."""
    assert (bootstrap_dir / "agentcore.tf").exists()


def test_agentcore_tf_defines_execution_role(bootstrap_dir):
    """Test that agentcore.tf defines the IAM execution role."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    pattern = r'resource\s+"aws_iam_role"\s+"agentcore_execution"'
    assert re.search(pattern, content) is not None


def test_agentcore_role_trusts_bedrock_service(bootstrap_dir):
    """Test that agentcore role trust policy allows bedrock-agentcore service."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "bedrock-agentcore.amazonaws.com" in content


def test_agentcore_role_allows_assume_role(bootstrap_dir):
    """Test that agentcore role allows sts:AssumeRole action."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "sts:AssumeRole" in content


def test_agentcore_role_has_source_account_condition(bootstrap_dir):
    """Test that agentcore role has aws:SourceAccount condition."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "aws:SourceAccount" in content


def test_agentcore_role_has_source_arn_condition(bootstrap_dir):
    """Test that agentcore role has aws:SourceArn condition."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "aws:SourceArn" in content


def test_agentcore_tf_defines_managed_policy_attachment(bootstrap_dir):
    """Test that agentcore.tf defines the managed policy attachment."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    pattern = r'resource\s+"aws_iam_role_policy_attachment"\s+"agentcore_managed"'
    assert re.search(pattern, content) is not None


def test_agentcore_policy_attachment_uses_bedrock_full_access(bootstrap_dir):
    """Test that policy attachment uses BedrockAgentCoreFullAccess."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert "BedrockAgentCoreFullAccess" in content


def test_agentcore_tf_defines_inline_policy(bootstrap_dir):
    """Test that agentcore.tf defines the inline execution policy."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    pattern = r'resource\s+"aws_iam_role_policy"\s+"agentcore_execution"'
    assert re.search(pattern, content) is not None


def test_agentcore_inline_policy_has_correct_name(bootstrap_dir):
    """Test that inline policy has correct name."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert 'name = "AgentCoreExecutionPolicy"' in content


def test_agentcore_role_has_managed_by_tag(bootstrap_dir):
    """Test that agentcore role has ManagedBy tag."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert 'ManagedBy = "terraform"' in content


def test_agentcore_role_has_stack_tag(bootstrap_dir):
    """Test that agentcore role has Stack tag."""
    agentcore_tf = bootstrap_dir / "agentcore.tf"
    content = agentcore_tf.read_text()
    assert 'Stack     = "bootstrap"' in content
