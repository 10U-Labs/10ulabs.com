provider "aws" {
  region = local.aws_region

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = local.github_repo_full
      Stack      = "image_for_ecs_runners"
    }
  }
}
