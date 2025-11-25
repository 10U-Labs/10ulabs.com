module "central_logs" {
  source = "./modules/central_logs"

  bucket_name    = module.config.central_logs_bucket_name
  aws_account_id = module.config.aws_account_id
}
