"""Tests for ECR repository configuration and lifecycle policies."""
import json


def test_ecr_repository_exists(ecr_client, config):
    """Verify ECR repository exists."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecr_lifecycle_policy_exists(ecr_client, config):
    """Verify ECR repository has lifecycle policy configured."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    assert "lifecyclePolicyText" in response


def test_ecr_lifecycle_policy_has_latest_rule(ecr_client, config):
    """Verify ECR lifecycle policy has rule for latest tag."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    tag_prefix = ["latest"]
    latest_rules = [r for r in rules if r.get("selection", {}).get("tagPrefixList") == tag_prefix]
    assert len(latest_rules) == 1


def test_ecr_lifecycle_policy_has_stable_rule(ecr_client, config):
    """Verify ECR lifecycle policy has rule for stable tag."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    tag_prefix = ["stable"]
    stable_rules = [r for r in rules if r.get("selection", {}).get("tagPrefixList") == tag_prefix]
    assert len(stable_rules) == 1


def test_ecr_lifecycle_policy_has_untagged_rule(ecr_client, config):
    """Verify ECR lifecycle policy has rule for untagged images."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    untagged = [r for r in rules if r.get("selection", {}).get("tagStatus") == "untagged"]
    assert len(untagged) == 1


def test_ecr_lifecycle_policy_has_catchall_rule(ecr_client, config):
    """Verify ECR lifecycle policy has catchall rule."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
    policy = json.loads(response["lifecyclePolicyText"])
    rules = policy["rules"]
    any_rules = [r for r in rules if r.get("selection", {}).get("tagStatus") == "any"]
    assert len(any_rules) == 1


def test_ecr_repository_image_scanning_enabled(ecr_client, config):
    """Verify ECR repository has image scanning enabled."""
    repository_name = config["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    scan_config = response["repositories"][0]["imageScanningConfiguration"]["scanOnPush"]
    assert scan_config is True
