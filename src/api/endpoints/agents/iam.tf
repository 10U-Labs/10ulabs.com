# IAM Roles and Policies for Agent Runtime

# ===================================================================
# AgentCore Execution Role - Used by Bedrock AgentCore Runtime
# ===================================================================

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

# Broad permissions - all agents share the same capabilities
# The prompt controls what each agent actually does
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

# ===================================================================
# Agent Lambda Role (shared by all agent Lambdas)
# ===================================================================

resource "aws_iam_role" "webhook_lambda" {
  name = "${local.resource_prefix}AgentLambdaRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "webhook_lambda_logs" {
  name = "AgentLambdaLogsPolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = [
        "${aws_cloudwatch_log_group.webhook_lambda.arn}:*",
        "${aws_cloudwatch_log_group.scanner_lambda.arn}:*",
        "${aws_cloudwatch_log_group.invoker_lambda.arn}:*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "webhook_lambda_sqs" {
  name = "AgentLambdaSQSPolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = [
        aws_sqs_queue.webhook_ingress.arn,
        aws_sqs_queue.scanner.arn,
        aws_sqs_queue.invoker_ingress.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy" "webhook_lambda_ssm" {
  name = "AgentLambdaSSMPolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ]
      Resource = [
        local.github_app_ssm_arns.id,
        local.github_app_ssm_arns.installation_id,
        local.github_app_ssm_arns.private_key,
      ]
    }]
  })
}

resource "aws_iam_role_policy" "webhook_lambda_agentcore" {
  name = "AgentLambdaAgentCorePolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock-agentcore:InvokeAgentRuntime"
      ]
      Resource = [
        aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn,
        "${aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "webhook_lambda_kms" {
  name = "AgentLambdaKMSPolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = module.shared.kms_lambda_key_arn
    }]
  })
}

# S3 permissions for Lambda to read prompts
resource "aws_iam_role_policy" "webhook_lambda_s3" {
  name = "AgentLambdaS3Policy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.prompts.arn,
        "${aws_s3_bucket.prompts.arn}/*"
      ]
    }]
  })
}

# ===================================================================
# AgentCore Additional Permissions
# ===================================================================

# Guardrails permissions for AgentCore runtime
resource "aws_iam_role_policy" "agentcore_guardrails" {
  name = "AgentCoreGuardrailsPolicy"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:ApplyGuardrail",
        "bedrock:GetGuardrail"
      ]
      Resource = [
        aws_bedrock_guardrail.agents.guardrail_arn,
        "${aws_bedrock_guardrail.agents.guardrail_arn}/*"
      ]
    }]
  })
}

# Memory permissions for AgentCore runtime
resource "aws_iam_role_policy" "agentcore_memory" {
  name = "AgentCoreMemoryPolicy"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:GetMemory",
          "bedrock-agentcore:PutMemory",
          "bedrock-agentcore:DeleteMemory",
          "bedrock-agentcore:ListMemories"
        ]
        Resource = [
          aws_bedrockagentcore_memory.agents.arn,
          "${aws_bedrockagentcore_memory.agents.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = [
          aws_opensearchserverless_collection.memory.arn
        ]
      }
    ]
  })
}

# S3 permissions for AgentCore runtime to read prompts
resource "aws_iam_role_policy" "agentcore_s3" {
  name = "AgentCoreS3Policy"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.prompts.arn,
        "${aws_s3_bucket.prompts.arn}/*"
      ]
    }]
  })
}
