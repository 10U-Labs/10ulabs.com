resource "aws_s3_bucket" "analytics" {
  bucket = "${lower(local.resource_prefix)}-sessions-analytics"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-analytics"
  })
}

resource "aws_s3_bucket_versioning" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    id     = "expire-old-exports"
    status = "Enabled"

    expiration {
      days = 90
    }

    filter {
      prefix = "exports/"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "export_lambda" {
  name = local.export_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = local.export_role_name
  })
}

resource "aws_iam_role_policy_attachment" "export_lambda_basic" {
  role       = aws_iam_role.export_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "export_permissions" {
  name = "ExportPermissions"
  role = aws_iam_role.export_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:ExportTableToPointInTime"
        ]
        Resource = [aws_dynamodb_table.events.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload"
        ]
        Resource = ["${aws_s3_bucket.analytics.arn}/*"]
      }
    ]
  })
}

data "archive_file" "export_lambda" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/export_lambda.zip"

  source {
    content  = file("${path.module}/lambda/exporter/handler.py")
    filename = "handler.py"
  }
}

resource "aws_lambda_function" "export" {
  function_name    = local.export_function_name
  role             = aws_iam_role.export_lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  filename         = data.archive_file.export_lambda.output_path
  source_code_hash = data.archive_file.export_lambda.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      DYNAMODB_TABLE_ARN = aws_dynamodb_table.events.arn
      S3_BUCKET          = aws_s3_bucket.analytics.bucket
      S3_PREFIX          = "exports/events"
    }
  }

  tags = merge(local.common_tags, {
    Name = local.export_function_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.export_lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "export_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.export.function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SessionsExport-Logs"
  })
}

resource "aws_scheduler_schedule" "daily_export" {
  name       = "${local.resource_prefix}-SessionsDailyExport"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 5 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.export.arn
    role_arn = aws_iam_role.scheduler.arn
  }
}

resource "aws_iam_role" "scheduler" {
  name = local.scheduler_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = local.scheduler_role_name
  })
}

resource "aws_iam_role_policy" "scheduler_invoke" {
  name = "InvokeLambda"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.export.arn
    }]
  })
}

resource "terraform_data" "initial_export" {
  triggers_replace = [aws_lambda_function.export.arn]

  provisioner "local-exec" {
    command = "aws lambda invoke --function-name ${aws_lambda_function.export.function_name} --region ${local.aws_region} /dev/null"
  }

  depends_on = [
    aws_lambda_function.export,
    aws_iam_role_policy.export_permissions,
    aws_s3_bucket.analytics
  ]
}
