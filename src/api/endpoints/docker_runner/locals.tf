locals {
  lambda_function_name = "${module.shared.resource_prefix}docker-runner-handler"
  lambda_handler       = "handler.lambda_handler"
  lambda_runtime       = "python3.12"
  lambda_timeout       = 30
  lambda_memory_size   = 256
}
