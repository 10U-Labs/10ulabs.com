"""Terraform unit tests for s3.tf.

These tests verify S3 bucket configurations for security and compliance.
"""

import re

import hcl2


def find_resource(tf_content, resource_type, resource_name):
    """Find a parsed resource block by type and name."""
    for resource in hcl2.loads(tf_content).get('resource', []):
        if resource_name in resource.get(resource_type, {}):
            return resource[resource_type][resource_name]
    return None


def find_lifecycle_rule(lifecycle, rule_id):
    """Find a lifecycle rule by its id, since AWS does not promise rule order."""
    for rule in (lifecycle or {}).get('rule', []):
        if rule['id'] == rule_id:
            return rule
    return {}


class TestS3BucketsExist:
    """Test that expected S3 buckets are defined."""

    def test_ignored_events_archive_bucket_exists(self, s3_tf_content):
        """Verify ignored_events_archive S3 bucket is defined."""
        pattern = r'resource\s+"aws_s3_bucket"\s+"ignored_events_archive"'
        assert re.search(pattern, s3_tf_content), (
            "S3 bucket 'ignored_events_archive' not found in s3.tf"
        )

    def test_bucket_count_is_at_least_one(self, s3_tf_content):
        """Verify at least one S3 bucket is defined."""
        bucket_pattern = r'resource\s+"aws_s3_bucket"\s+"\w+"'
        bucket_count = len(re.findall(bucket_pattern, s3_tf_content))
        assert bucket_count >= 1, "Expected at least one S3 bucket"


class TestS3BucketVersioning:
    """Test S3 bucket versioning configurations."""

    def test_versioning_resource_exists(self, s3_tf_content):
        """Verify versioning resource is defined."""
        pattern = r'resource\s+"aws_s3_bucket_versioning"\s+"ignored_events_archive"'
        assert re.search(pattern, s3_tf_content), (
            "Versioning resource not found in s3.tf"
        )

    def test_versioning_is_suspended(self, s3_tf_content):
        """Verify versioning is suspended so no second copy of a key is kept."""
        versioning = find_resource(
            s3_tf_content, 'aws_s3_bucket_versioning', 'ignored_events_archive'
        )
        status = versioning['versioning_configuration'][0]['status']
        assert status == "Suspended", (
            f"Bucket versioning should be Suspended, got {status}"
        )


class TestS3BucketEncryption:
    """Test S3 bucket encryption configurations."""

    def test_encryption_resource_exists(self, s3_tf_content):
        """Verify server-side encryption resource is defined."""
        pattern = (
            r'resource\s+"aws_s3_bucket_server_side_encryption_configuration"'
            r'\s+"ignored_events_archive"'
        )
        assert re.search(pattern, s3_tf_content), (
            "Server-side encryption resource not found in s3.tf"
        )

    def test_encryption_uses_aes256(self, s3_tf_content):
        """Verify encryption uses AES256 algorithm."""
        assert 'sse_algorithm = "AES256"' in s3_tf_content, (
            "Bucket should use AES256 server-side encryption"
        )

    def test_bucket_key_is_enabled(self, s3_tf_content):
        """Verify bucket key is enabled for cost optimization."""
        assert 'bucket_key_enabled = true' in s3_tf_content, (
            "Bucket key should be enabled"
        )


class TestS3PublicAccessBlock:
    """Test S3 public access block configurations."""

    def test_public_access_block_exists(self, s3_tf_content):
        """Verify public access block resource is defined."""
        pattern = r'resource\s+"aws_s3_bucket_public_access_block"\s+"ignored_events_archive"'
        assert re.search(pattern, s3_tf_content), (
            "Public access block resource not found in s3.tf"
        )

    def test_block_public_acls_enabled(self, s3_tf_content):
        """Verify block_public_acls is enabled."""
        assert 'block_public_acls       = true' in s3_tf_content, (
            "block_public_acls should be true"
        )

    def test_block_public_policy_enabled(self, s3_tf_content):
        """Verify block_public_policy is enabled."""
        assert 'block_public_policy     = true' in s3_tf_content, (
            "block_public_policy should be true"
        )

    def test_ignore_public_acls_enabled(self, s3_tf_content):
        """Verify ignore_public_acls is enabled."""
        assert 'ignore_public_acls      = true' in s3_tf_content, (
            "ignore_public_acls should be true"
        )

    def test_restrict_public_buckets_enabled(self, s3_tf_content):
        """Verify restrict_public_buckets is enabled."""
        assert 'restrict_public_buckets = true' in s3_tf_content, (
            "restrict_public_buckets should be true"
        )


class TestS3LifecycleConfiguration:
    """Test S3 lifecycle configuration."""

    def test_lifecycle_configuration_exists(self, s3_tf_content):
        """Verify lifecycle configuration resource is defined."""
        pattern = r'resource\s+"aws_s3_bucket_lifecycle_configuration"\s+"ignored_events_archive"'
        assert re.search(pattern, s3_tf_content), (
            "Lifecycle configuration resource not found in s3.tf"
        )

    def test_lifecycle_rule_is_enabled(self, s3_tf_content):
        """Verify lifecycle rule is enabled."""
        pattern = r'status\s*=\s*"Enabled"'
        assert re.search(pattern, s3_tf_content), (
            "Lifecycle rule should be enabled"
        )

    def test_transition_to_glacier_configured(self, s3_tf_content):
        """Verify transition to Glacier storage class is configured."""
        assert 'storage_class = "GLACIER"' in s3_tf_content, (
            "Lifecycle should transition objects to GLACIER"
        )

    def test_expiration_configured(self, s3_tf_content):
        """Verify object expiration is configured."""
        pattern = r'expiration\s*\{'
        assert re.search(pattern, s3_tf_content), (
            "Lifecycle should have expiration configured"
        )

    def test_noncurrent_version_expiration_configured(self, s3_tf_content):
        """Verify noncurrent version expiration is configured."""
        pattern = r'noncurrent_version_expiration\s*\{'
        assert re.search(pattern, s3_tf_content), (
            "Lifecycle should have noncurrent_version_expiration configured"
        )

    def test_delete_markers_are_expired(self, s3_tf_content):
        """Verify a rule removes the delete marker an expiry leaves behind."""
        lifecycle = find_resource(
            s3_tf_content, 'aws_s3_bucket_lifecycle_configuration', 'ignored_events_archive'
        )
        rule = find_lifecycle_rule(lifecycle, 'expire-delete-markers')
        expiration = (rule.get('expiration') or [{}])[0]
        assert expiration.get('expired_object_delete_marker') is True, (
            "Lifecycle needs an 'expire-delete-markers' rule that expires delete markers"
        )


class TestS3NamingConventions:
    """Test S3 naming conventions."""

    def test_bucket_name_uses_resource_prefix(self, s3_tf_content):
        """Verify bucket name uses local.resource_prefix."""
        pattern = r'bucket\s*=\s*lower\("\$\{local\.resource_prefix\}'
        assert re.search(pattern, s3_tf_content), (
            "Bucket name should use local.resource_prefix (lowercased)"
        )

    def test_bucket_name_is_lowercased(self, s3_tf_content):
        """Verify bucket name uses lower() function for S3 naming compliance."""
        assert 'lower(' in s3_tf_content, (
            "Bucket name should use lower() for S3 naming compliance"
        )


class TestS3Tags:
    """Test S3 resource tagging."""

    def test_bucket_has_tags(self, s3_tf_content):
        """Verify S3 bucket has tags defined."""
        pattern = r'tags\s*=\s*merge\(local\.common_tags'
        assert re.search(pattern, s3_tf_content), (
            "S3 bucket should have tags using local.common_tags"
        )

    def test_tags_use_common_tags(self, s3_tf_content):
        """Verify tags reference local.common_tags for consistency."""
        assert 'local.common_tags' in s3_tf_content, (
            "Tags should reference local.common_tags"
        )
