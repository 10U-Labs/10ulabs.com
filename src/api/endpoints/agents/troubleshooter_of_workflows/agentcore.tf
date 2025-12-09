# AgentCore Runtime for Troubleshooter of Workflows Agent
resource "aws_bedrockagentcore_agent_runtime" "troubleshooter_of_workflows" {
  agent_runtime_name = replace(local.stack_name, "-", "_")
  description        = "Troubleshooter of Workflows Agent - analyzes failures and creates fix PRs"
  role_arn           = aws_iam_role.agent_execution.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${data.terraform_remote_state.agents_shared.outputs.ecr_repository_url}:${local.image_tag}"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  environment_variables = {
    AWS_REGION         = local.aws_region
    AWS_DEFAULT_REGION = local.aws_region
  }

  tags = merge(local.common_tags, {
    Name = local.stack_name
  })
}
