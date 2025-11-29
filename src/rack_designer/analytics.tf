resource "aws_s3_bucket" "analytics" {
  bucket = "${lower(local.resource_prefix)}-rack-designer-analytics"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-designer-analytics"
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
  name = "${lower(local.resource_prefix)}_rack_designer_analytics"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-designer-analytics"
  })
}

resource "aws_iam_role" "glue_crawler" {
  name = "${local.resource_prefix}-RackDesignerGlueCrawler-Role"

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
    Name = "${local.resource_prefix}-RackDesignerGlueCrawler-Role"
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
  name          = "${local.resource_prefix}-rack-designer-events"
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
    Name = "${local.resource_prefix}-rack-designer-events-crawler"
  })
}

resource "aws_iam_role" "export_lambda" {
  name = "${local.resource_prefix}-RackDesignerExport-Role"

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
    Name = "${local.resource_prefix}-RackDesignerExport-Role"
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
  function_name    = "${local.resource_prefix}-RackDesignerExport"
  role             = aws_iam_role.export_lambda.arn
  handler          = "export_handler.lambda_handler"
  runtime          = "python3.13"
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
    Name = "${local.resource_prefix}-RackDesignerExport"
  })
}

resource "aws_cloudwatch_log_group" "export_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.export.function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-RackDesignerExport-Logs"
  })
}

resource "aws_scheduler_schedule" "daily_export" {
  name       = "${local.resource_prefix}-RackDesignerDailyExport"
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
  name = "${local.resource_prefix}-RackDesignerScheduler-Role"

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
    Name = "${local.resource_prefix}-RackDesignerScheduler-Role"
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

resource "aws_quicksight_data_source" "athena" {
  data_source_id = "rack-designer-analytics"
  aws_account_id = local.aws_account_id
  name           = "Rack Designer Analytics"
  type           = "ATHENA"

  parameters {
    athena {
      work_group = "primary"
    }
  }

  permission {
    actions = [
      "quicksight:DescribeDataSource",
      "quicksight:DescribeDataSourcePermissions",
      "quicksight:PassDataSource",
      "quicksight:UpdateDataSource",
      "quicksight:UpdateDataSourcePermissions"
    ]
    principal = "arn:aws:quicksight:${local.aws_region}:${local.aws_account_id}:user/default/${module.shared.admin_iam_user}"
  }

  ssl_properties {
    disable_ssl = false
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-designer-quicksight"
  })
}
