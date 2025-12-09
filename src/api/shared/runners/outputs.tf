# VPC Outputs
output "vpc_id" {
  description = "ID of the runners VPC"
  value       = aws_vpc.main.id
}

output "vpc_public_subnet_ids" {
  description = "Comma-separated list of public subnet IDs"
  value       = join(",", aws_subnet.public[*].id)
}

# Security Group Outputs
output "runner_security_group_id" {
  description = "ID of the runner security group"
  value       = aws_security_group.runner.id
}
