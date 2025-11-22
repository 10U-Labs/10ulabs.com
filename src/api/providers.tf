provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      ManagedBy  = "Terraform"
      Project    = "10UF"
      Repository = "10U-Labs-LLC/10ulabs.com"
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
      Repository = "10U-Labs-LLC/10ulabs.com"
      Stack      = "api"
    }
  }
}

provider "github" {
  token = data.aws_ssm_parameter.github_pat.value
  owner = "10U-Labs-LLC"
}
