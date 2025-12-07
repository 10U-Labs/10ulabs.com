locals {
  # Lambda function names - centrally defined for ARN construction
  lambda_function_names = {
    catchall              = "TenULabsCatchAllHandler"
    contact               = "TenULabsContactHandler"
    ec2_runner            = "TenULabs-EC2RunnerHandler"
    ecs_runner            = "TenULabsEcsRunnerHandler"
    echo                  = "TenULabsEchoHandler"
    health                = "TenULabsHealthHandler"
    image_for_ec2_runners = "TenULabsImageForEC2RunnersHandler"
    image_for_ecs_runners = "TenULabsImageForEcsRunnersHandler"
    rack_designer         = "TenULabsRackDesignerHandler"
    runners               = "TenULabsWebhookHandler"
    simulation_soc        = "TenULabsSimulationSocHandler"
  }

  # Helper to construct Lambda ARN from function name
  lambda_arn_prefix = "arn:aws:lambda:${local.aws_region}:${local.aws_account_id}:function"

  # Helper to construct API Gateway integration ARN from Lambda ARN
  apigw_integration_prefix = "arn:aws:apigateway:${local.aws_region}:lambda:path/2015-03-31/functions"

  # Construct all integration ARNs directly from function names
  catchall_integration_arn  = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.catchall}/invocations"
  contact_arn               = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.contact}/invocations"
  ec2_runner_arn            = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.ec2_runner}/invocations"
  ecs_runner_arn            = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.ecs_runner}/invocations"
  echo_arn                  = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.echo}/invocations"
  health_arn                = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.health}/invocations"
  image_for_ec2_runners_arn = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.image_for_ec2_runners}/invocations"
  image_for_ecs_runners_arn = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.image_for_ecs_runners}/invocations"
  rack_designer_arn         = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.rack_designer}/invocations"
  runners_arn               = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.runners}/invocations"
  simulation_soc_arn        = "${local.apigw_integration_prefix}/${local.lambda_arn_prefix}:${local.lambda_function_names.simulation_soc}/invocations"

  openapi_spec = templatefile("${path.module}/../../www/api/openapi.yml", {
    CatchAllHandlerArn           = local.catchall_integration_arn
    ContactHandlerArn            = local.contact_arn
    EcsRunnerHandlerArn          = local.ecs_runner_arn
    EC2RunnerHandlerArn          = local.ec2_runner_arn
    EchoHandlerArn               = local.echo_arn
    HealthHandlerArn             = local.health_arn
    ImageForEcsRunnersHandlerArn = local.image_for_ecs_runners_arn
    ImageForEC2RunnersHandlerArn = local.image_for_ec2_runners_arn
    RackDesignerHandlerArn       = local.rack_designer_arn
    RunnersHandlerArn            = local.runners_arn
    SimulationSocHandlerArn      = local.simulation_soc_arn
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

resource "aws_lambda_permission" "catchall_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.catchall_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*"
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

resource "null_resource" "api_gateway_propagation_wait" {
  depends_on = [
    aws_api_gateway_stage.prod
  ]

  triggers = {
    deployment_id = aws_api_gateway_deployment.main.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      N=0
      MAX_N=8
      SUCCESS=false
      while [ $N -le $MAX_N ]; do
        # Poll /health endpoint with GET - it falls back to CatchAllHandler
        # when health Lambda doesn't exist, which returns 404 (valid response)
        HTTP_STATUS=$(curl -s -o /dev/null -w "%%{http_code}" -X GET \
          "https://${local.api_fqdn}/health" || echo "000")
        # Accept 200 (health Lambda exists) or 404 (CatchAllHandler fallback)
        # Both indicate API Gateway is deployed and functioning
        if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
          echo "API Gateway is ready (status: $HTTP_STATUS)"
          SUCCESS=true
          N=$((MAX_N + 1))
        else
          DELAY=$((1 << N))
          echo "Attempt $((N + 1))/$((MAX_N + 1)): API returned status $HTTP_STATUS, waiting $${DELAY}s..."
          sleep $DELAY
          N=$((N + 1))
        fi
      done
      if [ "$SUCCESS" = "false" ]; then
        echo "ERROR: API Gateway not ready after ~8.5 minutes" >&2
        exit 1
      fi
    EOT
  }
}
