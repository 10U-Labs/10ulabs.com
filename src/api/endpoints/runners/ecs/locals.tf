locals {
  aws_account_id             = module.common.aws_account_id
  aws_region                 = module.common.aws_region
  ecs_execution_role_name    = "${module.common.resource_prefix}EcsRunnerExecutionRole"
  ecs_task_role_name         = "${module.common.resource_prefix}EcsRunnerTaskRole"
  lambda_execution_role_name = "${module.common.resource_prefix}EcsRunnerHandlerServiceRole"
  lambda_function_name       = module.common.lambda_handler_names.ecs_runner
  lambda_handler             = "handler.lambda_handler"
  lambda_memory_size         = 256
  lambda_runtime             = "python3.12"
  lambda_timeout             = 30
}
