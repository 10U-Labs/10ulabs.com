# ECR Repository for Agent Container Images
#
# This repository stores container images for all Bedrock AgentCore agents:
# - workflow-fixer
# - agent-creator
# - test-auditor (code-reviewer)

resource "aws_ecr_repository" "agents" {
  name                 = local.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = true

  tags = merge(local.common_tags, {
    Name = local.ecr_repository_name
  })
}

# Repository policy to allow Bedrock AgentCore to pull images
# Required for AgentCore to validate ECR URIs during CreateAgentRuntime/UpdateAgentRuntime
resource "aws_ecr_repository_policy" "agents" {
  repository = aws_ecr_repository.agents.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowBedrockAgentCore"
      Effect = "Allow"
      Principal = {
        Service = "agentcore.bedrock.amazonaws.com"
      }
      Action = [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ]
    }]
  })
}

# Lifecycle policy for agent images
resource "aws_ecr_lifecycle_policy" "agents" {
  repository = aws_ecr_repository.agents.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 agent-creator images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["agent-creator-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 workflow-fixer images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["workflow-fixer-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 3
        description  = "Keep last 5 test-auditor images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["test-auditor-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 10
        description  = "Expire untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 20
        description  = "Expire all other images older than 7 days"
        selection = {
          tagStatus   = "any"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = { type = "expire" }
      }
    ]
  })
}
