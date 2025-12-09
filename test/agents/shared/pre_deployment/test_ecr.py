"""Pre-deployment tests for agents/shared ECR Terraform configuration."""
import re


def test_ecr_tf_defines_agents_repository(agents_shared_dir):
    """Test that ecr.tf defines the agents ECR repository."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_repository"\s+"agents"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_name_matches_shared_module(agents_shared_dir, shared_module_dir):
    """Test that ECR repository name matches the shared module output."""
    import re
    # Get expected name from shared module (single source of truth)
    shared_outputs = (shared_module_dir / "outputs.tf").read_text()
    match = re.search(r'output "ecr_repository_name_agents"[^}]+value\s*=\s*"([^"]+)"', shared_outputs)
    assert match, "Could not find ecr_repository_name_agents in shared module"
    expected_name = match.group(1)

    # Verify locals.tf uses the same name
    locals_tf = agents_shared_dir / "locals.tf"
    content = locals_tf.read_text()
    assert f'ecr_repository_name = "{expected_name}"' in content


def test_ecr_repository_has_scan_on_push(agents_shared_dir):
    """Test that ECR repository has scan_on_push enabled."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "scan_on_push = true" in content


def test_ecr_repository_policy_defined(agents_shared_dir):
    """Test that ECR repository policy is defined for Bedrock AgentCore access."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_repository_policy"\s+"agents"'
    assert re.search(pattern, content) is not None, (
        "ECR repository policy must be defined to allow Bedrock AgentCore "
        "to validate ECR URIs during CreateAgentRuntime/UpdateAgentRuntime"
    )


def test_ecr_repository_policy_allows_bedrock_agentcore(agents_shared_dir):
    """Test that ECR repository policy grants access to Bedrock AgentCore service."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert "agentcore.bedrock.amazonaws.com" in content, (
        "ECR repository policy must allow agentcore.bedrock.amazonaws.com "
        "service principal to pull images"
    )


def test_ecr_repository_policy_has_required_actions(agents_shared_dir):
    """Test that ECR repository policy includes all required ECR actions."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    required_actions = [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
    ]
    for action in required_actions:
        assert action in content, (
            f"ECR repository policy must include {action} action "
            "for Bedrock AgentCore to pull container images"
        )


def test_ecr_repository_has_aes256_encryption(agents_shared_dir):
    """Test that ECR repository uses AES256 encryption."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    assert 'encryption_type = "AES256"' in content


def test_ecr_lifecycle_policy_defined(agents_shared_dir):
    """Test that ECR lifecycle policy is defined."""
    ecr_tf = agents_shared_dir / "ecr.tf"
    content = ecr_tf.read_text()
    pattern = r'resource\s+"aws_ecr_lifecycle_policy"\s+"agents"'
    assert re.search(pattern, content) is not None
