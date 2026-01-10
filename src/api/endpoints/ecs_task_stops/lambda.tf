data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = local.function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Handler for ECS task stopped events"

  environment {
    variables = {
      RETRIES_QUEUE_URL = data.terraform_remote_state.github_workflows_retries.outputs.sqs_queue_url
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tracing_config {
    mode = "Active"
  }

  tags = merge(local.common_tags, {
    Name = local.function_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.function_name}Logs"
  })
}

# SQS event source mapping
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.main.arn
  function_name                      = aws_lambda_function.handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}
