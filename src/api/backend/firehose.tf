resource "aws_kinesis_firehose_delivery_stream" "cloudwatch_logs" {
  name        = "${local.resource_prefix}-CloudWatchLogs"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_cloudwatch_logs.arn
    bucket_arn = data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket

    prefix              = "cloudwatch-logs/api/"
    error_output_prefix = "cloudwatch-logs/api-errors/"

    buffering_size     = 5
    buffering_interval = 300

    compression_format = "GZIP"

    cloudwatch_logging_options {
      enabled = false
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CloudWatchLogs"
  })
}

resource "aws_iam_role" "firehose_cloudwatch_logs" {
  name = "${local.resource_prefix}-FirehoseCloudWatchLogs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "firehose.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-FirehoseCloudWatchLogs"
  })
}

resource "aws_iam_role_policy" "firehose_s3_access" {
  name = "S3Access"
  role = aws_iam_role.firehose_cloudwatch_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket,
          "${data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role" "cloudwatch_logs_firehose" {
  name = "${local.resource_prefix}-CloudWatchLogsFirehose"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "logs.${local.aws_region}.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        StringLike = {
          "aws:SourceArn" = "arn:aws:logs:${local.aws_region}:${local.aws_account_id}:*"
        }
      }
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CloudWatchLogsFirehose"
  })
}

resource "aws_iam_role_policy" "cloudwatch_logs_firehose_access" {
  name = "FirehoseAccess"
  role = aws_iam_role.cloudwatch_logs_firehose.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "firehose:PutRecord"
      Resource = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
    }]
  })
}
