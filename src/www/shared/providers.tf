provider "aws" {
  region = local.aws_region

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = local.github_repo_full
      Stack      = "website"
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
      Stack      = "website"
    }
  }
}
