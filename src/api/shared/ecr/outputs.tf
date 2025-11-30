output "repository_arn" {
  value = aws_ecr_repository.runner.arn
}

output "repository_name" {
  value = aws_ecr_repository.runner.name
}

output "repository_url" {
  value = aws_ecr_repository.runner.repository_url
}
