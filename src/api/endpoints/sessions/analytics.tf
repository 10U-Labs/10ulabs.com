resource "aws_s3_bucket" "analytics" {
  bucket = "${lower(local.resource_prefix)}-sessions-analytics"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-analytics"
  })
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

resource "aws_glue_catalog_database" "analytics" {
  name = "${lower(local.resource_prefix)}_sessions_analytics"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-analytics"
  })
}

resource "aws_iam_role" "glue_crawler" {
  name = local.glue_crawler_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = local.glue_crawler_role_name
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "S3Access"
  role = aws_iam_role.glue_crawler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      Resource = ["${aws_s3_bucket.analytics.arn}/*"]
    }]
  })
}

resource "aws_glue_crawler" "events" {
  name          = "${local.resource_prefix}-sessions-events"
  database_name = aws_glue_catalog_database.analytics.name
  role          = aws_iam_role.glue_crawler.arn
  schedule      = "cron(0 6 * * ? *)"

  s3_target {
    path = "s3://${aws_s3_bucket.analytics.bucket}/exports/events/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-events-crawler"
  })
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
  output_path = "${path.module}/lambdas/export_lambda.zip"

  source {
    content  = file("${path.module}/lambdas/export_handler.py")
    filename = "export_handler.py"
  }
}

resource "aws_lambda_function" "export" {
  function_name    = local.export_function_name
  role             = aws_iam_role.export_lambda.arn
  handler          = "export_handler.lambda_handler"
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

data "archive_file" "crawler_trigger" {
  type        = "zip"
  output_path = "${path.module}/lambdas/crawler_trigger.zip"

  source {
    content  = file("${path.module}/lambdas/crawler_trigger.py")
    filename = "crawler_trigger.py"
  }
}

resource "aws_iam_role" "crawler_trigger" {
  name = local.crawler_trigger_role_name

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
    Name = local.crawler_trigger_role_name
  })
}

resource "aws_iam_role_policy_attachment" "crawler_trigger_basic" {
  role       = aws_iam_role.crawler_trigger.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "crawler_trigger_glue" {
  name = "GlueAccess"
  role = aws_iam_role.crawler_trigger.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "glue:StartCrawler"
      Resource = aws_glue_crawler.events.arn
    }]
  })
}

resource "aws_lambda_function" "crawler_trigger" {
  function_name    = local.crawler_trigger_function_name
  role             = aws_iam_role.crawler_trigger.arn
  handler          = "crawler_trigger.lambda_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  filename         = data.archive_file.crawler_trigger.output_path
  source_code_hash = data.archive_file.crawler_trigger.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      CRAWLER_NAME = aws_glue_crawler.events.name
    }
  }

  tags = merge(local.common_tags, {
    Name = local.crawler_trigger_function_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.crawler_trigger.id]
  }
}

resource "aws_cloudwatch_log_group" "crawler_trigger" {
  name              = "/aws/lambda/${aws_lambda_function.crawler_trigger.function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SessionsCrawlerTrigger-Logs"
  })
}

resource "aws_cloudwatch_event_rule" "export_completed" {
  name = "${local.resource_prefix}-SessionsExportCompleted"

  event_pattern = jsonencode({
    source      = ["aws.dynamodb"]
    detail-type = ["DynamoDB Export Completed"]
    detail = {
      eventType   = ["ExportCompleted"]
      tableArn    = [aws_dynamodb_table.events.arn]
      exportState = ["COMPLETED"]
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SessionsExportCompleted"
  })
}

resource "aws_cloudwatch_event_target" "crawler_trigger" {
  rule = aws_cloudwatch_event_rule.export_completed.name
  arn  = aws_lambda_function.crawler_trigger.arn
}

resource "aws_lambda_permission" "eventbridge_crawler" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crawler_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.export_completed.arn
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
