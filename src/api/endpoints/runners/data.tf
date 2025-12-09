data "terraform_remote_state" "api_shared_runners" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/runners/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "terraform_remote_state" "api_shared_ecs_runner" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/ecs_runner/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "terraform_remote_state" "ec2_runner" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "ec2_runner/terraform.tfstate"
    region = module.shared.aws_region
  }

  defaults = {
    ec2_instance_profile_name    = ""
    ec2_instance_types           = []
    ec2_runner_ami_purpose_tag   = ""
    ec2_runner_ami_purpose_value = ""
    ec2_runner_ami_stable_tag    = ""
    ec2_runner_managed_by_tag    = ""
    ec2_runner_role_arn          = ""
    ec2_runner_role_name         = ""
    lambda_function_arn          = ""
    lambda_function_name         = ""
  }
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.shared.aws_region
  }

  defaults = {
    api_key_ssm_parameter_arn = ""
  }
}

data "terraform_remote_state" "ecs_runner" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/endpoints/ecs_runner/terraform.tfstate"
    region = module.shared.aws_region
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

data "aws_ssm_parameter" "github_pat" {
  name            = module.shared.ssm_github_pat_name
  with_decryption = true
}
