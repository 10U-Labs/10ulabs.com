"""Layer 4: State tests for www home page deployment.

Test that Terraform state matches AWS reality. For www_home, we verify
that www_common infrastructure is deployed and accessible.
"""


class TestWWWCommonState:
    """Layer 4: Verify www_common Terraform state is available."""

    def test_www_common_terraform_initialized(self, www_common_terraform_initialized):
        """Verify www_common terraform has been initialized."""
        is_initialized = www_common_terraform_initialized is True
        assert is_initialized, (
            "www_common terraform not initialized. "
            "Run terraform init in src/www/common/"
        )

    def test_www_common_outputs_available(self, www_common_outputs):
        """Verify www_common terraform outputs are available."""
        has_outputs = www_common_outputs is not None
        assert has_outputs, (
            "www_common terraform outputs not available. "
            "Run terraform apply in src/www/common/"
        )

    def test_bucket_name_output_exists(self, www_common_outputs):
        """Verify bucket_name output is available."""
        bucket_name = www_common_outputs.get("bucket_name")
        has_bucket_name = bucket_name is not None and len(bucket_name) > 0
        assert has_bucket_name, (
            "bucket_name output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )
