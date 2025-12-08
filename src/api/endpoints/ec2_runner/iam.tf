resource "aws_iam_role" "ec2_runner" {
  name = "GitHubSelfHostedRunnerEC2Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "GitHubSelfHostedRunnerEC2Role"
  })
}

resource "aws_iam_role_policy_attachment" "ec2_runner_ssm_policy" {
  role       = aws_iam_role.ec2_runner.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_runner_ecr_access" {
  name = "ECRAccess"
  role = aws_iam_role.ec2_runner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ecr:*"]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "ec2_runner_self_terminate" {
  name = "SelfTerminate"
  role = aws_iam_role.ec2_runner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:TerminateInstances"]
      Resource = ["*"]
      Condition = {
        StringEquals = {
          "ec2:ResourceTag/ManagedBy" = local.ec2_runner_managed_by_tag
        }
      }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_runner" {
  name = "GitHubSelfHostedRunnerInstanceProfile"
  role = aws_iam_role.ec2_runner.name

  tags = merge(local.common_tags, {
    Name = "GitHubSelfHostedRunnerInstanceProfile"
  })
}

resource "aws_iam_role" "lambda" {
  name = "${local.resource_prefix}-EC2RunnerLambda-Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-EC2RunnerLambda-Role"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "ec2_access" {
  name = "EC2Access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:CreateFleet",
        "ec2:CreateLaunchTemplate",
        "ec2:CreateTags",
        "ec2:DeleteLaunchTemplate",
        "ec2:DescribeImages",
        "ec2:DescribeInstances",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:RunInstances",
        "ec2:TerminateInstances"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "iam_pass_role" {
  name = "IAMPassRole"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["iam:PassRole"]
      Resource = [aws_iam_role.ec2_runner.arn]
      Condition = {
        StringEquals = {
          "iam:PassedToService" = "ec2.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "ssm_access" {
  name = "SSMAccess"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter"
      ]
      Resource = compact([
        module.shared.ssm_github_pat_arn,
        data.terraform_remote_state.api.outputs.api_key_ssm_parameter_arn
      ])
    }]
  })
}

resource "aws_iam_role_policy" "kms_access" {
  name = "KMSDecrypt"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "dynamodb_access" {
  count = data.terraform_remote_state.runners.outputs.workflow_runners_table_arn != "" ? 1 : 0
  name  = "DynamoDBAccess"
  role  = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ]
      Resource = [data.terraform_remote_state.runners.outputs.workflow_runners_table_arn]
    }]
  })
}
