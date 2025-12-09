# Consolidated ECR Repositories
#
# All ECR repositories are managed here in bootstrap to ensure:
# - Single source of truth for container registries
# - Consistent lifecycle policies
# - Centralized management

# Runner ECR Repository
# Used by: EC2 runners, ECS runners (Fargate)
resource "aws_ecr_repository" "runners" {
  name                 = "10ulabs"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = true

  tags = {
    Name      = "10ulabs"
    ManagedBy = "terraform"
    Purpose   = "runners"
  }
}

resource "aws_ecr_lifecycle_policy" "runners" {
  repository = aws_ecr_repository.runners.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only 1 latest tag"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep only 1 stable tag"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["stable"]
          countType     = "imageCountMoreThan"
          countNumber   = 1
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
        description  = "Expire all images older than 1 day"
        selection = {
          tagStatus   = "any"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      }
    ]
  })
}

# Agents ECR Repository
# Used by: Agent Creator, Workflow Fixer, Test Auditor
# Images are tagged with agent name prefix: agent-creator-*, workflow-fixer-*, test_auditor-*
resource "aws_ecr_repository" "agents" {
  name                 = "10ulabs-agents"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = true

  tags = {
    Name      = "10ulabs-agents"
    ManagedBy = "terraform"
    Purpose   = "agents"
  }
}

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
      }
    ]
  })
}
