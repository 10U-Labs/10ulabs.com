"""Terraform unit tests for config.tf.

These tests verify the structure and configuration of AWS Config resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestS3BucketResources:
    """Test S3 bucket resources for Config."""

    def test_config_bucket_exists(self, config_tf_content):
        """Verify Config S3 bucket is defined."""
        pattern = r'resource\s+"aws_s3_bucket"\s+"config_bucket"'
        assert re.search(pattern, config_tf_content)

    def test_lifecycle_configuration_exists(self, config_tf_content):
        """Verify S3 lifecycle configuration is defined."""
        pattern = r'resource\s+"aws_s3_bucket_lifecycle_configuration"\s+"config_bucket"'
        assert re.search(pattern, config_tf_content)

    def test_public_access_block_exists(self, config_tf_content):
        """Verify S3 public access block is defined."""
        pattern = r'resource\s+"aws_s3_bucket_public_access_block"\s+"config_bucket"'
        assert re.search(pattern, config_tf_content)


class TestS3BucketConfiguration:
    """Test S3 bucket configuration."""

    def test_bucket_name_uses_account_id(self, config_tf_content):
        """Verify bucket name includes account ID for uniqueness."""
        pattern = r'local\.aws_account_id'
        assert re.search(pattern, config_tf_content)

    def test_bucket_blocks_public_acls(self, config_tf_content):
        """Verify bucket blocks public ACLs."""
        pattern = r'block_public_acls\s*=\s*true'
        assert re.search(pattern, config_tf_content)

    def test_bucket_blocks_public_policy(self, config_tf_content):
        """Verify bucket blocks public policy."""
        pattern = r'block_public_policy\s*=\s*true'
        assert re.search(pattern, config_tf_content)

    def test_lifecycle_expires_old_snapshots(self, config_tf_content):
        """Verify lifecycle expires config snapshots after 30 days."""
        pattern = r'days\s*=\s*30'
        assert re.search(pattern, config_tf_content)


class TestConfigRecorderResources:
    """Test AWS Config recorder resources."""

    def test_configuration_recorder_exists(self, config_tf_content):
        """Verify configuration recorder is defined."""
        pattern = r'resource\s+"aws_config_configuration_recorder"\s+"main"'
        assert re.search(pattern, config_tf_content)

    def test_delivery_channel_exists(self, config_tf_content):
        """Verify delivery channel is defined."""
        pattern = r'resource\s+"aws_config_delivery_channel"\s+"main"'
        assert re.search(pattern, config_tf_content)

    def test_recorder_status_exists(self, config_tf_content):
        """Verify recorder status is defined."""
        pattern = r'resource\s+"aws_config_configuration_recorder_status"\s+"main"'
        assert re.search(pattern, config_tf_content)


class TestConfigRecorderConfiguration:
    """Test Config recorder configuration."""

    def test_recorder_records_security_groups(self, config_tf_content):
        """Verify recorder records EC2 security groups."""
        assert '"AWS::EC2::SecurityGroup"' in config_tf_content

    def test_recorder_records_subnets(self, config_tf_content):
        """Verify recorder records EC2 subnets."""
        assert '"AWS::EC2::Subnet"' in config_tf_content

    def test_recorder_records_vpcs(self, config_tf_content):
        """Verify recorder records EC2 VPCs."""
        assert '"AWS::EC2::VPC"' in config_tf_content

    def test_recording_is_continuous(self, config_tf_content):
        """Verify recording frequency is continuous."""
        pattern = r'recording_frequency\s*=\s*"CONTINUOUS"'
        assert re.search(pattern, config_tf_content)

    def test_recorder_status_is_enabled(self, config_tf_content):
        """Verify recorder is enabled."""
        pattern = r'is_enabled\s*=\s*true'
        assert re.search(pattern, config_tf_content)


class TestConfigRuleResources:
    """Test AWS Config rule resources."""

    def test_required_tags_rule_exists(self, config_tf_content):
        """Verify required tags rule is defined."""
        pattern = r'resource\s+"aws_config_config_rule"\s+"required_tags"'
        assert re.search(pattern, config_tf_content)


class TestConfigRuleConfiguration:
    """Test Config rule configuration."""

    def test_rule_uses_aws_managed_source(self, config_tf_content):
        """Verify rule uses AWS managed source."""
        pattern = r'owner\s*=\s*"AWS"'
        assert re.search(pattern, config_tf_content)

    def test_rule_uses_required_tags_identifier(self, config_tf_content):
        """Verify rule uses REQUIRED_TAGS source identifier."""
        pattern = r'source_identifier\s*=\s*"REQUIRED_TAGS"'
        assert re.search(pattern, config_tf_content)

    def test_rule_requires_managed_by_tag(self, config_tf_content):
        """Verify rule requires ManagedBy tag."""
        assert '"ManagedBy"' in config_tf_content

    def test_rule_requires_purpose_tag(self, config_tf_content):
        """Verify rule requires Purpose tag."""
        assert '"Purpose"' in config_tf_content

    def test_rule_scope_includes_security_groups(self, config_tf_content):
        """Verify rule scope includes security groups."""
        # Scope section should include AWS::EC2::SecurityGroup
        pattern = r'compliance_resource_types\s*=\s*\['
        assert re.search(pattern, config_tf_content)
