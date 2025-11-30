locals {
  ecr_repository_name = module.shared.ecr_repository_name

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ecr"
  }
}
