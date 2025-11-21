module "cloudtrail" {
  source = "./modules/cloudtrail"

  trail_name                         = var.cloudtrail_name
  aws_account_id                     = var.aws_account_id
  aws_region                         = var.aws_region
  cloudtrail_bucket_name             = var.cloudtrail_bucket_name
  cloudtrail_access_logs_bucket_name = var.cloudtrail_access_logs_bucket_name
  cloudtrail_log_group_name          = var.cloudtrail_log_group_name
  cloudtrail_iam_role_name           = var.cloudtrail_iam_role_name
}
