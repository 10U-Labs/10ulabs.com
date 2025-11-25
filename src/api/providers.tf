provider "aws" {
  region = module.shared.aws_region

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = local.github_repo_full
      Stack      = "api"
    }
  }
}

provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = local.github_repo_full
      Stack      = "api"
    }
  }
}

provider "github" {
  token = data.aws_ssm_parameter.github_pat.value
  owner = module.shared.github_org
}
