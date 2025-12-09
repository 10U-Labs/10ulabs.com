"""Post-deployment integration tests for agents/shared ECR configuration."""
import json
import re
from pathlib import Path

# Add repo root to path to access shared module
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def _get_expected_ecr_name():
    """Get expected ECR repository name from shared module (single source of truth)."""
    shared_outputs = (SHARED_MODULE_DIR / "outputs.tf").read_text()
    match = re.search(
        r'output "ecr_repository_name_agents"[^}]+value\s*=\s*"([^"]+)"',
        shared_outputs
    )
    if not match:
        raise ValueError("Could not find ecr_repository_name_agents in shared module")
    return match.group(1)


def test_agents_ecr_repository_exists(ecr_client):
    """Test that the agents ECR repository exists."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    assert len(response["repositories"]) == 1


def test_agents_ecr_repository_has_scan_on_push_enabled(ecr_client):
    """Test that scan on push is enabled for the agents repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["imageScanningConfiguration"]["scanOnPush"] is True


def test_agents_ecr_repository_has_encryption_enabled(ecr_client):
    """Test that encryption is enabled for the agents repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert "encryptionConfiguration" in repo


def test_agents_ecr_repository_encryption_type_is_aes256(ecr_client):
    """Test that the agents repository uses AES256 encryption."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["encryptionConfiguration"]["encryptionType"] == "AES256"


def test_agents_ecr_repository_image_tag_mutability_is_mutable(ecr_client):
    """Test that image tag mutability is set to MUTABLE."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["imageTagMutability"] == "MUTABLE"


def test_agents_ecr_repository_has_managed_by_tag(ecr_client):
    """Test that the agents repository has the ManagedBy tag."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo_arn = response["repositories"][0]["repositoryArn"]
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag["Key"]: tag["Value"] for tag in tags_response["tags"]}
    assert tags.get("ManagedBy") == "terraform"


def test_agents_ecr_lifecycle_policy_exists(ecr_client):
    """Test that a lifecycle policy exists for the agents ECR repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    assert "lifecyclePolicyText" in response


def test_agents_ecr_lifecycle_policy_has_agent_creator_rule(ecr_client):
    """Test that the lifecycle policy has a rule for agent-creator."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_agent_creator_rule = any(
        "agent-creator-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_agent_creator_rule


def test_agents_ecr_lifecycle_policy_has_troubleshooter_of_workflows_rule(ecr_client):
    """Test that the lifecycle policy has a rule for troubleshooter-of-workflows."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_troubleshooter_of_workflows_rule = any(
        "troubleshooter-of-workflows-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_troubleshooter_of_workflows_rule


def test_agents_ecr_lifecycle_policy_has_test_auditor_rule(ecr_client):
    """Test that the lifecycle policy has a rule for test-auditor."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_test_auditor_rule = any(
        "test-auditor-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_test_auditor_rule


def test_agents_ecr_get_authorization_token_succeeds(ecr_client):
    """Verify current credentials can get ECR authorization token."""
    response = ecr_client.get_authorization_token()
    assert "authorizationData" in response
    assert len(response["authorizationData"]) > 0
    auth_data = response["authorizationData"][0]
    assert "authorizationToken" in auth_data
    assert auth_data["authorizationToken"]
