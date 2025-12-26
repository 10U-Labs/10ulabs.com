"""Tests for firehose.tf Terraform configuration."""

from pathlib import Path


def _get_terraform_path() -> Path:
    """Get the path to firehose.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "firehose.tf"


def test_firehose_terraform_file_exists():
    """Verify that firehose.tf file exists."""
    firehose_file = _get_terraform_path()
    assert firehose_file.exists()


def test_firehose_delivery_stream_resource_exists():
    """Verify that Firehose delivery stream resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_kinesis_firehose_delivery_stream" "cloudwatch_logs"' in content


def test_firehose_role_resource_exists():
    """Verify that Firehose IAM role resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "firehose_cloudwatch_logs"' in content


def test_firehose_s3_policy_resource_exists():
    """Verify that Firehose S3 policy resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "firehose_s3_access"' in content


def test_cloudwatch_logs_role_resource_exists():
    """Verify that CloudWatch Logs IAM role resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "cloudwatch_logs_firehose"' in content


def test_cloudwatch_logs_firehose_access_policy_exists():
    """Verify that CloudWatch Logs Firehose access policy exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "cloudwatch_logs_firehose_access"' in content


def test_firehose_destination_is_extended_s3():
    """Verify that Firehose destination is extended_s3."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'destination = "extended_s3"' in content


def test_firehose_s3_prefix_is_cloudwatch_logs_api():
    """Verify that Firehose S3 prefix is cloudwatch-logs/api/."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'prefix              = "cloudwatch-logs/api/"' in content


def test_firehose_error_output_prefix_is_cloudwatch_logs_api_errors():
    """Verify that Firehose error output prefix is cloudwatch-logs/api-errors/."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'error_output_prefix = "cloudwatch-logs/api-errors/"' in content


def test_firehose_buffering_size_is_5():
    """Verify that Firehose buffering size is 5."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'buffering_size     = 5' in content


def test_firehose_buffering_interval_is_300():
    """Verify that Firehose buffering interval is 300."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'buffering_interval = 300' in content


def test_firehose_compression_is_gzip():
    """Verify that Firehose compression is GZIP."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'compression_format = "GZIP"' in content


def test_firehose_cloudwatch_logging_disabled():
    """Verify that Firehose CloudWatch logging is disabled."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'enabled = false' in content


def test_firehose_role_trusts_firehose_service():
    """Verify that Firehose role trusts firehose.amazonaws.com."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'Service = "firehose.amazonaws.com"' in content


def test_cloudwatch_logs_role_trusts_logs_service():
    """Verify that CloudWatch Logs role trusts logs service."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert 'logs.${local.aws_region}.amazonaws.com' in content


def test_firehose_s3_policy_has_put_object():
    """Verify that Firehose S3 policy has PutObject permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:PutObject"' in content


def test_firehose_s3_policy_has_abort_multipart_upload():
    """Verify that Firehose S3 policy has AbortMultipartUpload permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:AbortMultipartUpload"' in content


def test_firehose_s3_policy_has_get_bucket_location():
    """Verify that Firehose S3 policy has GetBucketLocation permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:GetBucketLocation"' in content


def test_firehose_s3_policy_has_get_object():
    """Verify that Firehose S3 policy has GetObject permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:GetObject"' in content


def test_firehose_s3_policy_has_list_bucket():
    """Verify that Firehose S3 policy has ListBucket permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:ListBucket"' in content


def test_firehose_s3_policy_has_list_bucket_multipart_uploads():
    """Verify that Firehose S3 policy has ListBucketMultipartUploads permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"s3:ListBucketMultipartUploads"' in content


def test_cloudwatch_logs_firehose_access_has_put_record():
    """Verify that CloudWatch Logs Firehose access has PutRecord permission."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"firehose:PutRecord"' in content


def test_firehose_uses_central_logs_bucket():
    """Verify that Firehose uses central logs bucket."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    bucket_ref = 'data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket'
    assert bucket_ref in content


def test_firehose_role_has_name_tag():
    """Verify that Firehose role has name tag."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"${local.resource_prefix}-FirehoseCloudWatchLogs"' in content


def test_cloudwatch_logs_role_has_name_tag():
    """Verify that CloudWatch Logs role has name tag."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    assert '"${local.resource_prefix}-CloudWatchLogsFirehose"' in content
