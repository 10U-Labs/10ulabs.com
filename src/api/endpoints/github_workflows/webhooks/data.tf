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

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    api_key_ssm_parameter_arn         = ""
    cloudwatch_logs_firehose_role_arn = ""
    firehose_cloudwatch_logs_arn      = ""
  }
}

data "terraform_remote_state" "ec2_runner" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/endpoints/runners/ec2/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    ec2_runner_managed_by_tag = ""
  }
}

data "terraform_remote_state" "ecs_runner" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/endpoints/runners/ecs/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    cluster_arn              = ""
    cluster_name             = ""
    container_name           = ""
    execution_role_arn       = ""
    fargate_cpu_architecture = ""
    task_definition_arn      = ""
    task_role_arn            = ""
  }
}

data "terraform_remote_state" "runners" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/endpoints/runners/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    sqs_dlq_name = ""
  }
}

data "aws_ssm_parameter" "github_pat" {
  name            = module.common.ssm_github_pat_name
  with_decryption = true
}
