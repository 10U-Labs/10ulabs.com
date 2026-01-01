data "terraform_remote_state" "bootstrap" {
  backend = "s3"
  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "bootstrap/terraform.tfstate"
    region = module.common.aws_region
  }
}

data "terraform_remote_state" "api_common_networking" {
  backend = "s3"
  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/common/networking/terraform.tfstate"
    region = module.common.aws_region
  }
}

data "terraform_remote_state" "api_common_docker_repository" {
  backend = "s3"
  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/common/docker_repository/terraform.tfstate"
    region = module.common.aws_region
  }
}

data "terraform_remote_state" "api_common_routing" {
  backend = "s3"
  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    api_fqdn       = ""
    api_gateway_id = ""
  }
}

data "archive_file" "lambda" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/lambda/clients.py")
    filename = "clients.py"
  }
  source {
    content  = file("${path.module}/lambda/responses.py")
    filename = "responses.py"
  }
  source {
    content  = file("${path.module}/lambda/validation.py")
    filename = "validation.py"
  }
  source {
    content  = file("${path.module}/lambda/github.py")
    filename = "github.py"
  }
  source {
    content  = file("${path.module}/lambda/fargate_ops.py")
    filename = "fargate_ops.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/aws_clients/__init__.py")
    filename = "aws_clients.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/github_runner_api/__init__.py")
    filename = "github_runner_api.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/infra_validation/__init__.py")
    filename = "infra_validation.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/lambda_http/__init__.py")
    filename = "lambda_http.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${path.module}/../../../../../etc/runners.json")
    filename = "etc/runners.json"
  }
  output_path = "${path.module}/.terraform/lambda.zip"
}
