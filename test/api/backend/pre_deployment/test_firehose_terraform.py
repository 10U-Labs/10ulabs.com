from pathlib import Path


def test_firehose_terraform_file_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    assert firehose_file.exists()


def test_firehose_delivery_stream_resource_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_kinesis_firehose_delivery_stream" "cloudwatch_logs"' in content


def test_firehose_role_resource_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "firehose_cloudwatch_logs"' in content


def test_firehose_s3_policy_resource_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "firehose_s3_access"' in content


def test_cloudwatch_logs_role_resource_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "cloudwatch_logs_firehose"' in content


def test_cloudwatch_logs_firehose_access_policy_exists():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "cloudwatch_logs_firehose_access"' in content


def test_firehose_destination_is_extended_s3():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'destination = "extended_s3"' in content


def test_firehose_s3_prefix_is_cloudwatch_logs_api():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'prefix              = "cloudwatch-logs/api/"' in content


def test_firehose_error_output_prefix_is_cloudwatch_logs_api_errors():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'error_output_prefix = "cloudwatch-logs/api-errors/"' in content


def test_firehose_buffering_size_is_5():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'buffering_size     = 5' in content


def test_firehose_buffering_interval_is_300():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'buffering_interval = 300' in content


def test_firehose_compression_is_gzip():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'compression_format = "GZIP"' in content


def test_firehose_cloudwatch_logging_disabled():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'enabled = false' in content


def test_firehose_role_trusts_firehose_service():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'Service = "firehose.amazonaws.com"' in content


def test_cloudwatch_logs_role_trusts_logs_service():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'logs.${local.aws_region}.amazonaws.com' in content


def test_firehose_s3_policy_has_put_object():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:PutObject"' in content


def test_firehose_s3_policy_has_abort_multipart_upload():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:AbortMultipartUpload"' in content


def test_firehose_s3_policy_has_get_bucket_location():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:GetBucketLocation"' in content


def test_firehose_s3_policy_has_get_object():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:GetObject"' in content


def test_firehose_s3_policy_has_list_bucket():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:ListBucket"' in content


def test_firehose_s3_policy_has_list_bucket_multipart_uploads():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"s3:ListBucketMultipartUploads"' in content


def test_cloudwatch_logs_firehose_access_has_put_record():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"firehose:PutRecord"' in content


def test_firehose_uses_central_logs_bucket():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket' in content


def test_firehose_role_has_name_tag():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"${local.resource_prefix}-FirehoseCloudWatchLogs"' in content


def test_cloudwatch_logs_role_has_name_tag():
    firehose_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "firehose.tf"
    with open(firehose_file, encoding="utf-8") as f:
        content = f.read()
    assert '"${local.resource_prefix}-CloudWatchLogsFirehose"' in content
