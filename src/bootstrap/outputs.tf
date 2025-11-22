output "cloudtrail_bucket" {
  value = module.cloudtrail.bucket_name
}

output "cloudtrail_name" {
  value = module.cloudtrail.trail_name
}

output "github_actions_role_arn" {
  value = module.github_oidc.github_actions_role_arn
}

output "hosted_zone_id" {
  value = module.domain.hosted_zone_id
}

output "oidc_provider_arn" {
  value = module.github_oidc.oidc_provider_arn
}

output "state_bucket_arn" {
  value = aws_s3_bucket.terraform_state.arn
}

output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}
