# ECR Repository for the agent container
resource "aws_ecr_repository" "test_auditor" {
  name                 = "10ulabs/test-auditor-agent"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# AgentCore Runtime - the containerized agent
resource "aws_bedrockagentcore_agent_runtime" "test_auditor" {
  agent_runtime_name = local.agent_name
  description        = "Test Auditor Agent - audits and fixes pre-deployment integration tests"

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.test_auditor.repository_url}:latest"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  role_arn = aws_iam_role.agentcore_runtime.arn

  tags = local.common_tags
}

# AgentCore Gateway for external invocation
resource "aws_bedrockagentcore_gateway" "test_auditor" {
  name            = "${local.agent_name}Gateway"
  description     = "Gateway for Test Auditor Agent"
  protocol_type   = "MCP"
  authorizer_type = "AWS_IAM"

  protocol_configuration {
    mcp {
      instructions       = local.agent_instruction
      search_type        = "DEFAULT"
      supported_versions = ["1.0.0"]
    }
  }

  tags = local.common_tags
}

# Gateway Target to connect gateway to runtime
resource "aws_bedrockagentcore_gateway_target" "test_auditor" {
  gateway_identifier = aws_bedrockagentcore_gateway.test_auditor.gateway_id
  name               = "${local.agent_name}Target"
  description        = "Connect gateway to test auditor runtime"

  target_configuration {
    mcp {
      lambda {
        lambda_arn  = aws_lambda_function.action_group.arn
        tool_schema = file("${path.module}/tool_schema.json")
      }
    }
  }
}
