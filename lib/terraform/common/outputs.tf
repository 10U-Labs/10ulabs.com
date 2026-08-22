output "admin_iam_user" {
  value = "jdrowne"
}

output "aws_account_id" {
  value = local.aws_account_id
}

output "aws_region" {
  value = local.aws_region
}

output "domain_name" {
  value = "10ulabs.com"
}

output "github_org" {
  value = "10U-Labs"
}

output "name_for_central_logs_bucket" {
  value = "10ulabs-central-logs-us-east-2"
}

output "name_for_github_repo" {
  value = "10ulabs.com"
}

output "name_for_terraform_state_bucket" {
  value = "10ulabs-terraform-state-us-east-2"
}

output "resource_prefix" {
  value = local.resource_prefix
}

output "lambda_handler_names" {
  value = local.lambda_handler_names
}

output "ssm_github_pat_name" {
  value = local.ssm_github_pat_name
}

output "github_app" {
  value = local.github_app
}

output "kms_lambda_key_arn" {
  value = "arn:aws:kms:${local.aws_region}:${local.aws_account_id}:key/*"
}
