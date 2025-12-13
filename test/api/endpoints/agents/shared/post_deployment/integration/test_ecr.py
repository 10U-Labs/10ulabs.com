"""Post-deployment integration tests for agents/shared ECR configuration."""
import json


def test_agents_ecr_repository_exists(ecr_client, ecr_repository_name):
    """Test that the agents ECR repository exists."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    assert len(response["repositories"]) == 1


def test_agents_ecr_repository_has_scan_on_push_enabled(ecr_client, ecr_repository_name):
    """Test that scan on push is enabled for the agents repository."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    repo = response["repositories"][0]
    assert repo["imageScanningConfiguration"]["scanOnPush"] is True


def test_agents_ecr_repository_has_encryption_enabled(ecr_client, ecr_repository_name):
    """Test that encryption is enabled for the agents repository."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    repo = response["repositories"][0]
    assert "encryptionConfiguration" in repo


def test_agents_ecr_repository_encryption_type_is_aes256(ecr_client, ecr_repository_name):
    """Test that the agents repository uses AES256 encryption."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    repo = response["repositories"][0]
    assert repo["encryptionConfiguration"]["encryptionType"] == "AES256"


def test_agents_ecr_repository_image_tag_mutability_is_mutable(ecr_client, ecr_repository_name):
    """Test that image tag mutability is set to MUTABLE."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    repo = response["repositories"][0]
    assert repo["imageTagMutability"] == "MUTABLE"


def test_agents_ecr_repository_has_managed_by_tag(ecr_client, ecr_repository_name):
    """Test that the agents repository has the ManagedBy tag."""
    response = ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    repo_arn = response["repositories"][0]["repositoryArn"]
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag["Key"]: tag["Value"] for tag in tags_response["tags"]}
    assert tags.get("ManagedBy") == "terraform"


def test_agents_ecr_lifecycle_policy_exists(ecr_client, ecr_repository_name):
    """Test that a lifecycle policy exists for the agents ECR repository."""
    response = ecr_client.get_lifecycle_policy(repositoryName=ecr_repository_name)
    assert "lifecyclePolicyText" in response


def test_agents_ecr_lifecycle_policy_has_agent_creator_rule(ecr_client, ecr_repository_name):
    """Test that the lifecycle policy has a rule for agent-creator."""
    response = ecr_client.get_lifecycle_policy(repositoryName=ecr_repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_agent_creator_rule = any(
        "agent-creator-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_agent_creator_rule


def test_agents_ecr_lifecycle_policy_has_troubleshooter_of_workflows_rule(
    ecr_client, ecr_repository_name
):
    """Test that the lifecycle policy has a rule for troubleshooter-of-workflows."""
    response = ecr_client.get_lifecycle_policy(repositoryName=ecr_repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_troubleshooter_of_workflows_rule = any(
        "troubleshooter-of-workflows-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_troubleshooter_of_workflows_rule


def test_agents_ecr_lifecycle_policy_has_test_auditor_rule(ecr_client, ecr_repository_name):
    """Test that the lifecycle policy has a rule for test-auditor."""
    response = ecr_client.get_lifecycle_policy(repositoryName=ecr_repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_test_auditor_rule = any(
        "test-auditor-" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_test_auditor_rule


def test_agents_ecr_get_authorization_token_returns_auth_data(ecr_client):
    """Verify get_authorization_token returns authorizationData."""
    response = ecr_client.get_authorization_token()
    assert "authorizationData" in response


def test_agents_ecr_get_authorization_token_has_entries(ecr_client):
    """Verify authorizationData has at least one entry."""
    response = ecr_client.get_authorization_token()
    assert len(response["authorizationData"]) > 0


def test_agents_ecr_get_authorization_token_contains_token(ecr_client):
    """Verify authorization token is present and non-empty."""
    response = ecr_client.get_authorization_token()
    auth_data = response["authorizationData"][0]
    assert auth_data.get("authorizationToken")
