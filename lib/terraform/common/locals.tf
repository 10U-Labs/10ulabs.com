locals {
  aws_region          = "us-east-2"
  aws_account_id      = "781581267945"
  resource_prefix     = "TenULabs"
  ssm_github_pat_name = "/github/pat"

  # Runner configuration for self-hosted GitHub Actions runners
  runners_config = jsondecode(file("${path.module}/../../../etc/runners.json"))

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
    catchall                  = "${local.resource_prefix}CatchAllHandler"
    circuit_opens             = "${local.resource_prefix}CircuitOpensHandler"
    circuit_open_recoveries   = "${local.resource_prefix}CircuitOpenRecoveriesHandler"
    circuit_open_remediations = "${local.resource_prefix}CircuitOpenRemediationsHandler"
    contact                   = "${local.resource_prefix}ContactHandler"
    drift_recoveries          = "${local.resource_prefix}DriftRecoveriesHandler"
    ec2_runner                = "${local.resource_prefix}EC2RunnerHandler"
    ec2_spot_interruptions    = "${local.resource_prefix}Ec2SpotInterruptionsHandler"
    ecs_runner                = "${local.resource_prefix}EcsRunnerHandler"
    ecs_task_stops            = "${local.resource_prefix}EcsTaskStopsHandler"
    echo                      = "${local.resource_prefix}DiagnosticsHandler"
    github_workflows_retries  = "${local.resource_prefix}GithubWorkflowsRetriesHandler"
    health                    = "${local.resource_prefix}HealthHandler"
    image_for_ec2_runners     = "${local.resource_prefix}ImageForEC2RunnersHandler"
    image_for_ecs_runners     = "${local.resource_prefix}ImageForEcsRunnersHandler"
    rack_configurations       = "${local.resource_prefix}RackConfigurationsHandler"
    runners                   = "${local.resource_prefix}RunnersHandler"
    runners_cleanup           = "${local.resource_prefix}RunnersCleanupHandler"
    sessions                  = "${local.resource_prefix}SessionsHandler"
    simulation_soc            = "${local.resource_prefix}SimulationSocHandler"
    webhook                   = "${local.resource_prefix}WebhookHandler"
  }
}
