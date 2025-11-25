module "central_logs" {
  source = "./modules/central_logs"

  bucket_name    = local.central_logs_bucket_name
  aws_account_id = local.aws_account_id
}
