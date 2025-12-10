resource "aws_iam_role" "config_recorder" {
  name = "${local.resource_prefix}ConfigRecorderRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "config.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = self.name
  })
}

resource "aws_iam_role_policy_attachment" "config_recorder_policy" {
  role       = aws_iam_role.config_recorder.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_iam_role_policy" "config_recorder_s3" {
  name = "ConfigS3Delivery"
  role = aws_iam_role.config_recorder.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = ["${aws_s3_bucket.config_bucket.arn}/*"]
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketAcl"]
        Resource = [aws_s3_bucket.config_bucket.arn]
      }
    ]
  })
}

resource "aws_s3_bucket" "config_bucket" {
  bucket = lower("${local.resource_prefix}-config-${local.aws_account_id}")

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-config-bucket"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "config_bucket" {
  bucket = aws_s3_bucket.config_bucket.id

  rule {
    id     = "expire-old-config-snapshots"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket_public_access_block" "config_bucket" {
  bucket = aws_s3_bucket.config_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_config_configuration_recorder" "main" {
  name     = "${local.resource_prefix}-recorder"
  role_arn = aws_iam_role.config_recorder.arn

  recording_group {
    all_supported                 = false
    include_global_resource_types = false

    resource_types = [
      "AWS::EC2::SecurityGroup",
      "AWS::EC2::Subnet",
      "AWS::EC2::VPC"
    ]
  }

  recording_mode {
    recording_frequency = "CONTINUOUS"
  }

  depends_on = [
    aws_iam_role_policy.config_recorder_s3,
    aws_iam_role_policy_attachment.config_recorder_policy,
  ]
}

resource "aws_config_delivery_channel" "main" {
  name           = "${local.resource_prefix}-delivery"
  s3_bucket_name = aws_s3_bucket.config_bucket.id

  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

resource "aws_config_config_rule" "required_tags" {
  name = "${local.resource_prefix}-required-tags"

  source {
    owner             = "AWS"
    source_identifier = "REQUIRED_TAGS"
  }

  input_parameters = jsonencode({
    tag1Key = "ManagedBy"
    tag2Key = "Purpose"
  })

  scope {
    compliance_resource_types = [
      "AWS::EC2::SecurityGroup",
      "AWS::EC2::Subnet",
      "AWS::EC2::VPC"
    ]
  }

  depends_on = [aws_config_configuration_recorder.main]

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-required-tags-rule"
  })
}

resource "aws_cloudwatch_event_rule" "config_compliance_change" {
  name        = "${local.resource_prefix}-config-compliance-change"
  description = "Triggers on AWS Config compliance changes for infrastructure drift detection"

  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules Compliance Change"]
    detail = {
      configRuleName = [aws_config_config_rule.required_tags.name]
      newEvaluationResult = {
        complianceType = ["NON_COMPLIANT"]
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-config-compliance-change"
  })
}

resource "aws_cloudwatch_event_target" "drift_recovery" {
  rule      = aws_cloudwatch_event_rule.config_compliance_change.name
  target_id = "drift-recovery-sqs"
  arn       = aws_sqs_queue.drift_recovery.arn

  sqs_target {
    message_group_id = "drift-recovery"
  }

  input_transformer {
    input_paths = {
      configRuleName = "$.detail.configRuleName"
      resourceType   = "$.detail.resourceType"
      resourceId     = "$.detail.resourceId"
      awsRegion      = "$.detail.awsRegion"
    }
    input_template = <<EOF
{
  "source": "drift-recovery-trigger",
  "configRuleName": <configRuleName>,
  "resourceType": <resourceType>,
  "resourceId": <resourceId>,
  "awsRegion": <awsRegion>
}
EOF
  }
}
