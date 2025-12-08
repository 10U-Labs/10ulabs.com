resource "aws_bedrockagentcore_agent_runtime" "agent_creator" {
  agent_runtime_name = replace(local.stack_name, "-", "_")
  description        = "Agent Creator - creates new agents as needed"
  role_arn           = aws_iam_role.agent_execution.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agent.repository_url}:${local.image_tag}"
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
