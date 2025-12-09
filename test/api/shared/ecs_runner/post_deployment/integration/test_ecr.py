"""Post-deployment integration tests for api/shared/ecs_runner ECR configuration."""
import re
import sys
from pathlib import Path

# Add repo root to path to access shared module
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def _get_expected_ecr_name():
    """Get expected ECR repository name from shared module (single source of truth)."""
    shared_outputs = (SHARED_MODULE_DIR / "outputs.tf").read_text()
    match = re.search(r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"', shared_outputs)
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


def test_runners_ecr_lifecycle_policy_exists(ecr_client):
    """Test that a lifecycle policy exists for the runners ECR repository."""
    expected_name = _get_expected_ecr_name()
    response = ecr_client.get_lifecycle_policy(repositoryName=expected_name)
    assert "lifecyclePolicyText" in response
