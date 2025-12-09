# ECR Repository for ECS Runner Container Images
#
# This repository stores container images for GitHub self-hosted ECS Fargate runners.
# EC2 runners use custom AMIs instead of Docker images.

resource "aws_ecr_repository" "runners" {
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

# Lifecycle policy for runner images
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
