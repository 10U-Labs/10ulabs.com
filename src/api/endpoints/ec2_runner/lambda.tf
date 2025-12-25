data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${path.module}/../../../../etc/runners.json")
    filename = "etc/runners.json"
  }
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = module.shared.lambda_handler_names.ec2_runner
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Handler for /v1/ec2-runner API endpoints"

  environment {
    variables = {
      API_DOMAIN               = data.terraform_remote_state.runners.outputs.api_endpoint
      API_KEY_PARAMETER_NAME   = data.terraform_remote_state.api.outputs.api_key_ssm_parameter
      EC2_AMI_PURPOSE_TAG      = local.ec2_runner_ami_purpose_tag
      EC2_AMI_PURPOSE_VALUE    = local.ec2_runner_ami_purpose_value
      EC2_AMI_STABLE_TAG       = local.ec2_runner_ami_stable_tag
      EC2_IAM_INSTANCE_PROFILE = aws_iam_instance_profile.ec2_runner.name
      EC2_INSTANCE_TYPES       = join(",", var.ec2_instance_types)
      EC2_MANAGED_BY_TAG       = local.ec2_runner_managed_by_tag
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.runners.outputs.github_token_secret_name
      SECURITY_GROUPS          = data.terraform_remote_state.api_shared_networking.outputs.runner_security_group_id
      SUBNETS                  = data.terraform_remote_state.api_shared_networking.outputs.vpc_public_subnet_ids
      VPC_ID                   = data.terraform_remote_state.api_shared_networking.outputs.vpc_id
      WORKFLOW_RUNNERS_TABLE   = data.terraform_remote_state.runners.outputs.workflow_runners_table_name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.ec2_runner
  })

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${module.shared.lambda_handler_names.ec2_runner}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.ec2_runner}Logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
