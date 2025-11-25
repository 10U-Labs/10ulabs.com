module "cloudtrail" {
  source = "./modules/cloudtrail"

  trail_name                    = var.name_for_cloudtrail
  aws_account_id                = module.config.aws_account_id
  aws_region                    = module.config.aws_region
  name_for_cloudtrail_bucket    = var.name_for_cloudtrail_bucket
  central_logs_bucket_name      = module.central_logs.bucket_name
  name_for_cloudtrail_log_group = var.name_for_cloudtrail_log_group
  name_for_cloudtrail_iam_role  = var.name_for_cloudtrail_iam_role
}
