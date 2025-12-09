# ECR Repository Outputs
output "ecr_repository_arn" {
  description = "ARN of the runners ECR repository"
  value       = aws_ecr_repository.runners.arn
}

output "ecr_repository_name" {
  description = "Name of the runners ECR repository"
  value       = aws_ecr_repository.runners.name
}

output "ecr_repository_url" {
  description = "URL of the runners ECR repository"
  value       = aws_ecr_repository.runners.repository_url
}
