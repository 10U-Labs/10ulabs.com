locals {
  openapi_spec = templatefile("${path.module}/../../www/api/openapi.yml", {
    CatchAllHandlerArn              = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.catchall_handler.arn}/invocations"
    ContactHandlerArn               = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${data.terraform_remote_state.contact.outputs.lambda_function_arn}/invocations"
    EchoHandlerArn                  = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${data.terraform_remote_state.echo.outputs.lambda_function_arn}/invocations"
    HealthHandlerArn                = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${data.terraform_remote_state.health.outputs.lambda_function_arn}/invocations"
    ImageForDockerRunnersHandlerArn = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${data.terraform_remote_state.image_for_docker_runners.outputs.lambda_function_arn}/invocations"
    RackDesignerHandlerArn          = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${data.terraform_remote_state.rack_designer.outputs.lambda_function_arn}/invocations"
    RunnersHandlerArn               = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.runners_handler.arn}/invocations"
    V1HandlerArn                    = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.v1_handler.arn}/invocations"
  })
  spec_hash = substr(md5(local.openapi_spec), 0, 8)
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = var.api_gateway_log_group_name
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${var.api_gateway_name}-logs"
  })
}

resource "aws_api_gateway_rest_api" "main" {
  name = var.api_gateway_name

  body = local.openapi_spec

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(local.common_tags, {
    Name = var.api_gateway_name
  })
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = local.spec_hash
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_rest_api.main
  ]
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format          = "$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] \"$context.httpMethod $context.resourcePath $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"
  }

  xray_tracing_enabled = true

  tags = merge(local.common_tags, {
    Name = "prod"
  })

  depends_on = [aws_api_gateway_account.main]
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "*/*"

  settings {
    logging_level      = "INFO"
    data_trace_enabled = true
    metrics_enabled    = true
  }
}

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.stack_name}-api-gateway-cloudwatch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.stack_name}-api-gateway-cloudwatch"
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_lambda_permission" "v1_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.v1_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/${var.api_version}/*"
}

resource "aws_lambda_permission" "runners_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.runners_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/${var.api_version}/runners*"
}

resource "aws_lambda_permission" "catchall_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.catchall_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "health_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = data.terraform_remote_state.health.outputs.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/GET/health*"
}

resource "aws_lambda_permission" "echo_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = data.terraform_remote_state.echo.outputs.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/${var.api_version}/echo*"
}

resource "aws_lambda_permission" "contact_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = data.terraform_remote_state.contact.outputs.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/${var.api_version}/contact*"
}

resource "aws_lambda_permission" "image_for_docker_runners_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = data.terraform_remote_state.image_for_docker_runners.outputs.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/${var.api_version}/image-for-docker-runners*"
}

resource "random_password" "api_key" {
  length  = 32
  special = false
}

resource "aws_api_gateway_api_key" "main" {
  name    = "${var.stack_name}-api-key"
  enabled = true
  value   = random_password.api_key.result
}

resource "aws_api_gateway_usage_plan" "main" {
  name = "${var.stack_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.main.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}
