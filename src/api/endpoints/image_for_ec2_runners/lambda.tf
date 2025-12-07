data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = module.shared.lambda_handler_names.image_for_ec2_runners
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  description      = "Handler for /v1/image-for-ec2-runners API endpoints"

  environment {
    variables = {
      EC2_AMI_PURPOSE_TAG      = local.ami_purpose_tag
      EC2_AMI_PURPOSE_VALUE    = local.ami_purpose_value
      EC2_AMI_STABLE_TAG       = local.ami_stable_tag
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      SUBNETS                  = data.terraform_remote_state.api_backend.outputs.vpc_public_subnet_ids
      VPC_ID                   = data.terraform_remote_state.api_backend.outputs.vpc_id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.image_for_ec2_runners
  })
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${module.shared.lambda_handler_names.image_for_ec2_runners}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.image_for_ec2_runners}-logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api_backend.outputs.api_gateway_rest_api_id}/*"
}
