# Shared AgentCore Infrastructure
#
# This file defines the common IAM role used by all Bedrock AgentCore runtimes.
# Individual agents reference module.shared.agentcore.execution_role_arn instead
# of creating their own roles.

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
          "aws:SourceAccount" = module.shared.aws_account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:bedrock-agentcore:${module.shared.aws_region}:${module.shared.aws_account_id}:*"
        }
      }
    }]
  })

  tags = {
    Name      = module.shared.agentcore.execution_role_name
    ManagedBy = "terraform"
    Stack     = "bootstrap"
  }
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
