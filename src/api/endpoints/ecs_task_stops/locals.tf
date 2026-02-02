locals {
  resource_prefix  = module.common.resource_prefix

  function_name    = "${local.resource_prefix}EcsTaskStops"
  lambda_role_name = "${local.resource_prefix}EcsTaskStopsRole"
  rule_name        = "${local.resource_prefix}EcsTaskStoppedRule"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ecs-task-stops"
  }
}
