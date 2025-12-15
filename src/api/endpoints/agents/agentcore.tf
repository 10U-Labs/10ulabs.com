# AgentCore Runtime - Single runtime for all agents
#
# Agents are differentiated by the prompt passed at invocation time.
# The runtime loads prompts from the prompts/ directory in the container.

resource "aws_bedrockagentcore_agent_runtime" "runtime" {
  agent_runtime_name = replace(local.stack_name, "-", "_")
  description        = "Unified agent runtime - loads prompts dynamically"
  role_arn           = aws_iam_role.agentcore_execution.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agents.repository_url}:${local.image_tag}"
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

  depends_on = [
    aws_iam_role_policy.agentcore_execution,
    aws_iam_role_policy_attachment.agentcore_managed,
  ]
}
