def test_module_main_file_exists(module_path):
    assert (module_path / "main.tf").exists()


def test_module_variables_file_exists(module_path):
    assert (module_path / "variables.tf").exists()


def test_module_outputs_file_exists(module_path):
    assert (module_path / "outputs.tf").exists()


def test_module_versions_file_exists(module_path):
    assert (module_path / "versions.tf").exists()


def test_s3_bucket_resource_exists(main_tf_content):
    assert 'resource "aws_s3_bucket"' in main_tf_content


def test_s3_bucket_versioning_resource_exists(main_tf_content):
    assert 'resource "aws_s3_bucket_versioning"' in main_tf_content


def test_s3_bucket_versioning_is_disabled(main_tf_content):
    assert 'status = "Disabled"' in main_tf_content


def test_s3_bucket_public_access_block_exists(main_tf_content):
    assert 'resource "aws_s3_bucket_public_access_block"' in main_tf_content


def test_s3_bucket_public_access_block_blocks_acls(main_tf_content):
    assert 'block_public_acls       = true' in main_tf_content


def test_s3_bucket_public_access_block_blocks_policy(main_tf_content):
    assert 'block_public_policy     = true' in main_tf_content


def test_s3_bucket_public_access_block_ignores_acls(main_tf_content):
    assert 'ignore_public_acls      = true' in main_tf_content


def test_s3_bucket_public_access_block_restricts_buckets(main_tf_content):
    assert 'restrict_public_buckets = true' in main_tf_content


def test_s3_bucket_encryption_exists(main_tf_content):
    resource = 'resource "aws_s3_bucket_server_side_encryption_configuration"'
    assert resource in main_tf_content


def test_s3_bucket_encryption_uses_aes256(main_tf_content):
    assert 'sse_algorithm = "AES256"' in main_tf_content


def test_s3_bucket_logging_resource_exists(main_tf_content):
    assert 'resource "aws_s3_bucket_logging"' in main_tf_content


def test_s3_bucket_logging_is_optional(main_tf_content):
    assert 'count = var.central_logs_bucket != null' in main_tf_content


def test_bucket_name_variable_exists(variables_tf_content):
    assert 'variable "bucket_name"' in variables_tf_content


def test_central_logs_bucket_variable_exists(variables_tf_content):
    assert 'variable "central_logs_bucket"' in variables_tf_content


def test_bucket_id_output_exists(outputs_tf_content):
    assert 'output "bucket_id"' in outputs_tf_content


def test_bucket_arn_output_exists(outputs_tf_content):
    assert 'output "bucket_arn"' in outputs_tf_content


def test_module_declares_required_version(versions_tf_content):
    assert "required_version" in versions_tf_content


def test_module_declares_aws_provider(versions_tf_content):
    assert "hashicorp/aws" in versions_tf_content
