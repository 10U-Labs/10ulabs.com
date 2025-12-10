locals {
  aws_region          = "us-east-2"
  aws_account_id      = "781581267945"
  resource_prefix     = "TenULabs"
  ssm_github_pat_name = "/github/pat"

  # Runner configuration for self-hosted GitHub Actions runners
  runners_config = yamldecode(file("${path.module}/../../../../etc/runners.yml"))

  # AgentCore shared infrastructure
  agentcore = {
    execution_role_name = "${local.resource_prefix}AgentCoreExecutionRole"
    execution_role_arn  = "arn:aws:iam::${local.aws_account_id}:role/${local.resource_prefix}AgentCoreExecutionRole"
  }

  # GitHub App configuration
  github_app = {
    id              = "2436221"
    installation_id = "98653544"
    ssm_prefix      = "/github/app"
  }

  lambda_handler_names = {
    catchall              = "${local.resource_prefix}CatchAllHandler"
    contact               = "${local.resource_prefix}ContactHandler"
    ec2_runner            = "${local.resource_prefix}EC2RunnerHandler"
    ecs_runner            = "${local.resource_prefix}EcsRunnerHandler"
    echo                  = "${local.resource_prefix}EchoHandler"
    health                = "${local.resource_prefix}HealthHandler"
    image_for_ec2_runners = "${local.resource_prefix}ImageForEC2RunnersHandler"
    image_for_ecs_runners = "${local.resource_prefix}ImageForEcsRunnersHandler"
    rack_designer         = "${local.resource_prefix}RackDesignerHandler"
    webhook               = "${local.resource_prefix}WebhookHandler"
    simulation_soc        = "${local.resource_prefix}SimulationSocHandler"
  }
}
