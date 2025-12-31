# SSM Parameter for latest EC2 runner AMI ID
# This parameter is updated by the AMI build workflow and read by the EC2 runner Lambda
resource "aws_ssm_parameter" "ec2_runner_ami_latest" {
  name  = local.ssm_ec2_runner_ami_latest
  type  = "String"
  value = "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"
  tier  = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(local.common_tags, {
    Name = local.ssm_ec2_runner_ami_latest
  })
}
