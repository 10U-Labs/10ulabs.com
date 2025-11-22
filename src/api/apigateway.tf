locals {
  openapi_spec = templatefile("${path.module}/files/openapi.yml", {
    HealthHandlerArn   = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.health_handler.arn}/invocations"
    V1HandlerArn       = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.v1_handler.arn}/invocations"
    CatchAllHandlerArn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.catchall_handler.arn}/invocations"
    RunnersHandlerArn  = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.runners_handler.arn}/invocations"
  })
  spec_hash = substr(md5(local.openapi_spec), 0, 8)
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.stack_name}"
  retention_in_days = 30

  tags = {
    Name = "${var.stack_name}-api-gateway-logs"
  }
}

resource "aws_api_gateway_rest_api" "main" {
  name        = "TenULabsApi"
  description = "API Gateway for api.10ulabs.com"

  body = local.openapi_spec

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "TenULabsApi"
  }
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
    format          = "$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] \"$context.httpMethod $context.resourcePath $context.protocol\" $context.status $context.responseLength $context.requestId"
  }

  xray_tracing_enabled = true

  tags = {
    Name = "prod"
  }
}

resource "aws_lambda_permission" "health_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/GET/health"
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
