"""Post-deployment integration tests for api/shared/ecs_runner ECR configuration."""
import json
import re
from repo_utils import REPO_ROOT

# Add repo root to path to access shared module
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def _get_expected_ecr_name():
    """Get expected ECR repository name from shared module (single source of truth)."""
    shared_outputs = (SHARED_MODULE_DIR / "outputs.tf").read_text()
    pattern = r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"'
    match = re.search(pattern, shared_outputs)
    if not match:
        raise ValueError("Could not find ecr_repository_name_runners in shared module")
    return match.group(1)


def test_runners_ecr_repository_exists(ecr_client):
    """Test that the runners ECR repository exists."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    assert len(response["repositories"]) == 1


def test_runners_ecr_repository_has_scan_on_push_enabled(ecr_client):
    """Test that scan on push is enabled for the runners repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["imageScanningConfiguration"]["scanOnPush"] is True


def test_runners_ecr_repository_has_encryption_enabled(ecr_client):
    """Test that encryption is enabled for the runners repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert "encryptionConfiguration" in repo


def test_runners_ecr_repository_encryption_type_is_aes256(ecr_client):
    """Test that the runners repository uses AES256 encryption."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["encryptionConfiguration"]["encryptionType"] == "AES256"


def test_runners_ecr_repository_image_tag_mutability_is_mutable(ecr_client):
    """Test that image tag mutability is set to MUTABLE."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo = response["repositories"][0]
    assert repo["imageTagMutability"] == "MUTABLE"


def test_runners_ecr_repository_has_managed_by_tag(ecr_client):
    """Test that the runners repository has the ManagedBy tag."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.describe_repositories(repositoryNames=[expected_name])
    repo_arn = response["repositories"][0]["repositoryArn"]
    tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
    tags = {tag["Key"]: tag["Value"] for tag in tags_response["tags"]}
    assert tags.get("ManagedBy") == "terraform"


def test_runners_ecr_lifecycle_policy_exists(ecr_client):
    """Test that a lifecycle policy exists for the runners ECR repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    assert "lifecyclePolicyText" in response


def test_runners_ecr_lifecycle_policy_has_latest_rule(ecr_client):
    """Test that the lifecycle policy has a rule for latest tag."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_latest_rule = any(
        "latest" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_latest_rule


def test_runners_ecr_lifecycle_policy_has_stable_rule(ecr_client):
    """Test that the lifecycle policy has a rule for stable tag."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    policy = json.loads(response["lifecyclePolicyText"])
    has_stable_rule = any(
        "stable" in str(rule.get("selection", {}).get("tagPrefixList", []))
        for rule in policy["rules"]
    )
    assert has_stable_rule


def test_runners_ecr_get_authorization_token_returns_auth_data(ecr_client):
    """Verify get_authorization_token returns authorizationData."""
    response = ecr_client.get_authorization_token()
    assert "authorizationData" in response and len(response["authorizationData"]) > 0


def test_runners_ecr_get_authorization_token_contains_token(ecr_client):
    """Verify authorization data contains a non-empty token."""
    response = ecr_client.get_authorization_token()
    auth_data = response["authorizationData"][0]
    assert "authorizationToken" in auth_data and auth_data["authorizationToken"]
