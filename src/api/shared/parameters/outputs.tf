output "ssm_ec2_runner_ami_latest_name" {
  description = "SSM parameter name for latest EC2 runner AMI ID"
  value       = aws_ssm_parameter.ec2_runner_ami_latest.name
}

output "ssm_ec2_runner_ami_latest_arn" {
  description = "ARN of SSM parameter for latest EC2 runner AMI ID"
  value       = aws_ssm_parameter.ec2_runner_ami_latest.arn
}
