output "ec2_instance_profile_name" {
  value = aws_iam_instance_profile.ec2_runner.name
}

output "ec2_runner_ami_purpose_tag" {
  value = local.ec2_runner_ami_purpose_tag
}

output "ec2_runner_ami_purpose_value" {
  value = local.ec2_runner_ami_purpose_value
}

output "ec2_runner_ami_stable_tag" {
  value = local.ec2_runner_ami_stable_tag
}

output "ec2_runner_managed_by_tag" {
  value = local.ec2_runner_managed_by_tag
}

output "ec2_runner_role_arn" {
  value = aws_iam_role.ec2_runner.arn
}

output "ec2_runner_role_name" {
  value = aws_iam_role.ec2_runner.name
}

output "ec2_instance_types" {
  value = var.ec2_instance_types
}

output "lambda_function_arn" {
  value = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.handler.function_name
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.handler.invoke_arn
}

output "lambda_role_name" {
  value = aws_iam_role.lambda.name
}
