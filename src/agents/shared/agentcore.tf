# Shared AgentCore Infrastructure
#
# This file defines the common IAM role used by all Bedrock AgentCore runtimes.
# Individual agents reference this role via terraform_remote_state.

resource "aws_iam_role" "agentcore_execution" {
  name = module.shared.agentcore.execution_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AssumeRolePolicy"
      Effect = "Allow"
      Principal = {
        Service = "bedrock-agentcore.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = local.aws_account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:bedrock-agentcore:${local.aws_region}:${local.aws_account_id}:*"
        }
      }
    }]
  })

  tags = merge(local.common_tags, {
    Name = module.shared.agentcore.execution_role_name
  })
}

resource "aws_iam_role_policy_attachment" "agentcore_managed" {
  role       = aws_iam_role.agentcore_execution.name
  policy_arn = "arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess"
}

resource "aws_iam_role_policy" "agentcore_execution" {
  name = "AgentCoreExecutionPolicy"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "FullAccess"
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}
