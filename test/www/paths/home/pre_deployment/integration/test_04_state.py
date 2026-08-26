class TestWWWCommonState:
    def test_www_common_terraform_initialized(self, www_common_terraform_initialized):
        is_initialized = www_common_terraform_initialized is True
        assert is_initialized, (
            "www_common terraform not initialized. "
            "Run terraform init in src/www/common/"
        )

    def test_www_common_outputs_available(self, www_common_outputs):
        has_outputs = www_common_outputs is not None
        assert has_outputs, (
            "www_common terraform outputs not available. "
            "Run terraform apply in src/www/common/"
        )

    def test_bucket_name_output_exists(self, www_common_outputs):
        bucket_name = www_common_outputs.get("bucket_name")
        has_bucket_name = bucket_name is not None and len(bucket_name) > 0
        assert has_bucket_name, (
            "bucket_name output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )
