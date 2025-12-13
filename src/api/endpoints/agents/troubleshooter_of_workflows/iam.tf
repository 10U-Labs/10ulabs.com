# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ===================================================================
# Agent Execution Role - For AgentCore Runtime
# ===================================================================

resource "aws_iam_role" "agent_execution" {
  name = "${local.resource_prefix}TroubleshooterOfWorkflowsAgentExecutionRole"

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
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
        }
      }
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}TroubleshooterOfWorkflowsAgentExecutionRole"
  })
}

# Attach AWS managed policy for AgentCore
resource "aws_iam_role_policy_attachment" "agent_execution_managed" {
  role       = aws_iam_role.agent_execution.name
  policy_arn = "arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess"
}

# Inline policy for agent execution
resource "aws_iam_role_policy" "agent_execution" {
  name = "AgentCoreExecutionPolicy"
  role = aws_iam_role.agent_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR Access
      {
        Sid    = "ECRImageAccess"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = data.terraform_remote_state.agents_shared.outputs.ecr_repository_arn
      },
      {
        Sid      = "ECRTokenAccess"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      # CloudWatch Logs
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogStreams",
          "logs:CreateLogGroup",
          "logs:DescribeLogGroups",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
      },
      # X-Ray Tracing
      {
        Sid    = "XRayTracing"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      },
      # CloudWatch Metrics
      {
        Sid      = "CloudWatchMetrics"
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "bedrock-agentcore"
          }
        }
      },
      # Bedrock Model Invocation
      {
        Sid    = "BedrockModelInvocation"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      # Workload Access Tokens
      {
        Sid    = "GetAgentAccessToken"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:GetWorkloadAccessToken",
          "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
          "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
        ]
        Resource = [
          "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default",
          "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default/workload-identity/*"
        ]
      }
    ]
  })
}

# ===================================================================
# Webhook Lambda Role
# ===================================================================

resource "aws_iam_role" "webhook_lambda" {
  name = local.webhook_lambda_role_name

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
  name = "${local.lambda_name}LogsPolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.webhook_lambda.arn}:*"
    }]
  })
}

resource "aws_iam_role_policy" "webhook_lambda_ssm" {
  name = "${local.lambda_name}SSMPolicy"
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
  name = "${local.lambda_name}AgentCorePolicy"
  role = aws_iam_role.webhook_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock-agentcore:InvokeAgentRuntime"
      ]
      Resource = [
        aws_bedrockagentcore_agent_runtime.troubleshooter_of_workflows.agent_runtime_arn,
        "${aws_bedrockagentcore_agent_runtime.troubleshooter_of_workflows.agent_runtime_arn}/*"
      ]
    }]
  })
}
