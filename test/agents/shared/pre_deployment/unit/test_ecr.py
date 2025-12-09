"""Unit tests for agents/shared ECR Terraform configuration.

These tests verify the Terraform ECR configuration is correct
by parsing the ecr.tf file directly, without deploying.
"""

import re


class TestECRRepositoryResource:
    """Tests for the aws_ecr_repository.agents resource."""

    def test_ecr_tf_file_exists(self, agents_shared_dir):
        """Verify ecr.tf file exists."""
        ecr_tf = agents_shared_dir / "ecr.tf"
        assert ecr_tf.exists(), f"ecr.tf not found at {ecr_tf}"

    def test_ecr_repository_resource_exists(self, agents_shared_dir):
        """Verify the aws_ecr_repository.agents resource exists."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        pattern = r'resource\s+"aws_ecr_repository"\s+"agents"'
        assert re.search(pattern, content) is not None, (
            "aws_ecr_repository.agents resource not found in ecr.tf"
        )

    def test_ecr_repository_name_uses_local(self, agents_shared_dir):
        """Verify the repository name references local.ecr_repository_name."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "local.ecr_repository_name" in content, (
            "ECR repository should use local.ecr_repository_name for consistency"
        )

    def test_ecr_repository_name_matches_shared_module(
        self, agents_shared_dir, shared_module_dir
    ):
        """Verify ECR repository name matches the shared module output."""
        shared_outputs = (shared_module_dir / "outputs.tf").read_text()
        match = re.search(
            r'output "ecr_repository_name_agents"[^}]+value\s*=\s*"([^"]+)"',
            shared_outputs
        )
        assert match, "Could not find ecr_repository_name_agents in shared module"
        expected_name = match.group(1)

        locals_content = (agents_shared_dir / "locals.tf").read_text()
        assert f'ecr_repository_name = "{expected_name}"' in locals_content, (
            f"locals.tf should define ecr_repository_name = \"{expected_name}\""
        )


class TestECRRepositoryImageSettings:
    """Tests for ECR repository image configuration."""

    def test_image_tag_mutability_is_mutable(self, agents_shared_dir):
        """Verify image_tag_mutability is set to MUTABLE."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert 'image_tag_mutability = "MUTABLE"' in content, (
            "ECR repository image_tag_mutability should be MUTABLE"
        )

    def test_scan_on_push_enabled(self, agents_shared_dir):
        """Verify scan_on_push is enabled for security scanning."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "scan_on_push = true" in content, (
            "ECR repository should have scan_on_push = true for security"
        )


class TestECRRepositoryEncryption:
    """Tests for ECR repository encryption configuration."""

    def test_encryption_configuration_exists(self, agents_shared_dir):
        """Verify encryption_configuration block exists."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "encryption_configuration" in content, (
            "ECR repository should have encryption_configuration block"
        )

    def test_encryption_type_is_aes256(self, agents_shared_dir):
        """Verify encryption type is AES256."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert 'encryption_type = "AES256"' in content, (
            "ECR repository should use AES256 encryption"
        )


class TestECRRepositoryDeletion:
    """Tests for ECR repository deletion settings."""

    def test_force_delete_enabled(self, agents_shared_dir):
        """Verify force_delete is enabled for cleanup."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "force_delete = true" in content, (
            "ECR repository should have force_delete = true"
        )


class TestECRRepositoryTags:
    """Tests for ECR repository tagging."""

    def test_tags_use_common_tags(self, agents_shared_dir):
        """Verify tags merge with local.common_tags."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "local.common_tags" in content, (
            "ECR repository tags should merge with local.common_tags"
        )

    def test_name_tag_references_local(self, agents_shared_dir):
        """Verify Name tag references local.ecr_repository_name."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Name = local.ecr_repository_name" in content, (
            "ECR repository Name tag should use local.ecr_repository_name"
        )


class TestECRLifecyclePolicyResource:
    """Tests for the aws_ecr_lifecycle_policy.agents resource."""

    def test_lifecycle_policy_resource_exists(self, agents_shared_dir):
        """Verify the aws_ecr_lifecycle_policy.agents resource exists."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        pattern = r'resource\s+"aws_ecr_lifecycle_policy"\s+"agents"'
        assert re.search(pattern, content) is not None, (
            "aws_ecr_lifecycle_policy.agents resource not found in ecr.tf"
        )

    def test_lifecycle_policy_references_repository(self, agents_shared_dir):
        """Verify lifecycle policy references the repository."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "aws_ecr_repository.agents.name" in content, (
            "Lifecycle policy should reference aws_ecr_repository.agents.name"
        )


class TestECRLifecyclePolicyRulesAgentCreator:
    """Tests for agent-creator lifecycle policy rule."""

    def test_agent_creator_rule_exists(self, agents_shared_dir):
        """Verify lifecycle policy has a rule for agent-creator images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert '"agent-creator-"' in content, (
            "Lifecycle policy should have a rule for agent-creator- tag prefix"
        )

    def test_agent_creator_rule_keeps_5_images(self, agents_shared_dir):
        """Verify agent-creator rule keeps last 5 images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Keep last 5 agent-creator images" in content, (
            "Lifecycle policy should keep last 5 agent-creator images"
        )


class TestECRLifecyclePolicyRulesTroubleshooter:
    """Tests for troubleshooter-of-workflows lifecycle policy rule."""

    def test_troubleshooter_rule_exists(self, agents_shared_dir):
        """Verify lifecycle policy has a rule for troubleshooter-of-workflows images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert '"troubleshooter-of-workflows-"' in content, (
            "Lifecycle policy should have a rule for troubleshooter-of-workflows- tag prefix"
        )

    def test_troubleshooter_rule_keeps_5_images(self, agents_shared_dir):
        """Verify troubleshooter-of-workflows rule keeps last 5 images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Keep last 5 troubleshooter-of-workflows images" in content, (
            "Lifecycle policy should keep last 5 troubleshooter-of-workflows images"
        )


class TestECRLifecyclePolicyRulesTestAuditor:
    """Tests for test-auditor lifecycle policy rule."""

    def test_test_auditor_rule_exists(self, agents_shared_dir):
        """Verify lifecycle policy has a rule for test-auditor images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert '"test-auditor-"' in content, (
            "Lifecycle policy should have a rule for test-auditor- tag prefix"
        )

    def test_test_auditor_rule_keeps_5_images(self, agents_shared_dir):
        """Verify test-auditor rule keeps last 5 images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Keep last 5 test-auditor images" in content, (
            "Lifecycle policy should keep last 5 test-auditor images"
        )


class TestECRLifecyclePolicyRulesUntagged:
    """Tests for untagged images lifecycle policy rule."""

    def test_untagged_rule_exists(self, agents_shared_dir):
        """Verify lifecycle policy has a rule for untagged images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Expire untagged images after 1 day" in content, (
            "Lifecycle policy should expire untagged images after 1 day"
        )


class TestECRLifecyclePolicyRulesOther:
    """Tests for other images lifecycle policy rule."""

    def test_other_images_rule_exists(self, agents_shared_dir):
        """Verify lifecycle policy has a catch-all rule for other images."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "Expire all other images older than 7 days" in content, (
            "Lifecycle policy should expire other images older than 7 days"
        )


class TestECRLifecyclePolicyRulePriorities:
    """Tests for lifecycle policy rule priorities."""

    def test_agent_rules_have_higher_priority_than_cleanup(self, agents_shared_dir):
        """Verify agent-specific rules run before cleanup rules."""
        content = (agents_shared_dir / "ecr.tf").read_text()
        assert "rulePriority = 1" in content, "agent-creator should have priority 1"
        assert "rulePriority = 2" in content, "troubleshooter should have priority 2"
        assert "rulePriority = 3" in content, "test-auditor should have priority 3"
        assert "rulePriority = 10" in content, "untagged cleanup should have priority 10"
        assert "rulePriority = 20" in content, "catch-all cleanup should have priority 20"
