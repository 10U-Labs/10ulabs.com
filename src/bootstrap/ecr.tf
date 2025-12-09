# Consolidated ECR Repository
#
# Single ECR repository for all container images:
# - Runners: latest, stable tags
# - Agents: prefixed tags (agent-creator-*, troubleshooter-of-workflows-*, test-auditor-*)

resource "aws_ecr_repository" "main" {
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
  }
}

resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      # Runner images
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
      # Agent images
      {
        rulePriority = 3
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
        rulePriority = 4
        description  = "Keep last 5 troubleshooter-of-workflows images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["troubleshooter-of-workflows-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 5
        description  = "Keep last 5 test-auditor images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["test-auditor-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
      # Cleanup
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

# State migration: rename runners -> main
moved {
  from = aws_ecr_repository.runners
  to   = aws_ecr_repository.main
}

moved {
  from = aws_ecr_lifecycle_policy.runners
  to   = aws_ecr_lifecycle_policy.main
}

# State migration: remove agents repository (will be deleted)
# The agents repository resources are removed from config.
# Terraform will destroy them on next apply (force_delete=true was set).
