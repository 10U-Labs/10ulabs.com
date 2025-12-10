locals {
  aws_account_id       = module.shared.aws_account_id
  aws_region           = module.shared.aws_region
  lambda_function_name = module.shared.lambda_handler_names.ecs_runner
  lambda_handler       = "handler.lambda_handler"
  lambda_runtime       = "python3.12"
  lambda_timeout       = 30
  lambda_memory_size   = 256
}
