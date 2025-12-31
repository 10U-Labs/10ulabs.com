"""Layer 2: Configuration tests for api/common/docker_repository post-deployment.

Tests that resources have correct settings. Assumes existence tests passed.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""

import json

import pytest


pytestmark = pytest.mark.layer(2)


class TestECRSecurityConfiguration:
    """Layer 2: Verify ECR security configuration."""

    def test_runners_ecr_repository_has_scan_on_push_disabled(
        self, ecr_client, expected_ecr_name
    ):
        """Verify scan on push is disabled (ARM64 images not supported)."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        repo = response["repositories"][0]
        assert repo["imageScanningConfiguration"]["scanOnPush"] is False, (
            f"ECR repository '{expected_ecr_name}' should have scan_on_push disabled"
        )

    def test_runners_ecr_repository_has_encryption_enabled(
        self, ecr_client, expected_ecr_name
    ):
        """Verify encryption is enabled for the runners repository."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        repo = response["repositories"][0]
        assert "encryptionConfiguration" in repo, (
            f"ECR repository '{expected_ecr_name}' does not have encryption configured"
        )

    def test_runners_ecr_repository_encryption_type_is_aes256(
        self, ecr_client, expected_ecr_name
    ):
        """Verify the runners repository uses AES256 encryption."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        repo = response["repositories"][0]
        assert repo["encryptionConfiguration"]["encryptionType"] == "AES256", (
            f"ECR repository '{expected_ecr_name}' does not use AES256 encryption"
        )


class TestECRTagConfiguration:
    """Layer 2: Verify ECR tagging configuration."""

    def test_runners_ecr_repository_image_tag_mutability_is_mutable(
        self, ecr_client, expected_ecr_name
    ):
        """Verify image tag mutability is set to MUTABLE."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        repo = response["repositories"][0]
        assert repo["imageTagMutability"] == "MUTABLE", (
            f"ECR repository '{expected_ecr_name}' image tag mutability is not MUTABLE"
        )

    def test_runners_ecr_repository_has_managed_by_tag(
        self, ecr_client, expected_ecr_name
    ):
        """Verify the runners repository has the ManagedBy tag."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        repo_arn = response["repositories"][0]["repositoryArn"]
        tags_response = ecr_client.list_tags_for_resource(resourceArn=repo_arn)
        tags = {tag["Key"]: tag["Value"] for tag in tags_response["tags"]}
        assert tags.get("ManagedBy") == "terraform", (
            f"ECR repository '{expected_ecr_name}' missing 'ManagedBy: terraform' tag"
        )


class TestECRLifecycleConfiguration:
    """Layer 2: Verify ECR lifecycle policy configuration."""

    def test_runners_ecr_lifecycle_policy_has_latest_rule(
        self, ecr_client, expected_ecr_name
    ):
        """Verify the lifecycle policy has a rule for latest tag."""
        response = ecr_client.get_lifecycle_policy(repositoryName=expected_ecr_name)
        policy = json.loads(response["lifecyclePolicyText"])
        has_latest_rule = any(
            "latest" in str(rule.get("selection", {}).get("tagPrefixList", []))
            for rule in policy["rules"]
        )
        assert has_latest_rule, (
            f"ECR lifecycle policy for '{expected_ecr_name}' missing 'latest' rule"
        )

    def test_runners_ecr_lifecycle_policy_has_stable_rule(
        self, ecr_client, expected_ecr_name
    ):
        """Verify the lifecycle policy has a rule for stable tag."""
        response = ecr_client.get_lifecycle_policy(repositoryName=expected_ecr_name)
        policy = json.loads(response["lifecyclePolicyText"])
        has_stable_rule = any(
            "stable" in str(rule.get("selection", {}).get("tagPrefixList", []))
            for rule in policy["rules"]
        )
        assert has_stable_rule, (
            f"ECR lifecycle policy for '{expected_ecr_name}' missing 'stable' rule"
        )
