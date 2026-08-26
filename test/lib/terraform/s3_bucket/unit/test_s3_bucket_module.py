def test_module_files_exist(module_path):
    assert (
        (module_path / "main.tf").exists()
        and (module_path / "variables.tf").exists()
        and (module_path / "outputs.tf").exists()
    )


def test_s3_bucket_resource_exists(main_tf_content):
    assert 'resource "aws_s3_bucket"' in main_tf_content


def test_s3_bucket_versioning_resource_exists(main_tf_content):
    assert 'resource "aws_s3_bucket_versioning"' in main_tf_content


def test_s3_bucket_versioning_is_disabled(main_tf_content):
    assert 'status = "Disabled"' in main_tf_content


def test_s3_bucket_public_access_block_exists(main_tf_content):
    assert 'resource "aws_s3_bucket_public_access_block"' in main_tf_content


def test_s3_bucket_public_access_block_all_enabled(main_tf_content):
    assert (
        'block_public_acls       = true' in main_tf_content
        and 'block_public_policy     = true' in main_tf_content
        and 'ignore_public_acls      = true' in main_tf_content
        and 'restrict_public_buckets = true' in main_tf_content
    )


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
