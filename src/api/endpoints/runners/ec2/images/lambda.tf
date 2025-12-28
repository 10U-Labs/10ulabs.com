data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../../../lib/python/lambda_http/__init__.py")
    filename = "lambda_http.py"
  }
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = module.shared.lambda_handler_names.image_for_ec2_runners
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128
  description      = "Handler for /v1/runners/ec2/images API endpoints"

  environment {
    variables = {
      EC2_AMI_PURPOSE_TAG       = local.ami_purpose_tag
      EC2_AMI_PURPOSE_VALUE     = local.ami_purpose_value
      EC2_AMI_STABLE_TAG        = local.ami_stable_tag
      GITHUB_REPO               = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME  = module.shared.ssm_github_pat_name
      SSM_EC2_RUNNER_AMI_LATEST = module.shared.ssm_ec2_runner_ami_latest
      SUBNETS                   = data.terraform_remote_state.api_shared_routing.outputs.vpc_public_subnet_ids
      VPC_ID                    = data.terraform_remote_state.api_shared_routing.outputs.vpc_id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.image_for_ec2_runners
  })

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${module.shared.lambda_handler_names.image_for_ec2_runners}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.image_for_ec2_runners}Logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api_shared_routing.outputs.api_gateway_rest_api_id}/*"
}
