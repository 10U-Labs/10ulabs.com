provider "aws" {
  region = local.aws_region

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = local.github_repo_full
      Stack      = "runners"
    }
  }
}

provider "github" {
  token = data.aws_ssm_parameter.github_pat.value
  owner = local.github_org
}
