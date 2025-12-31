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

resource "aws_iam_role_policy" "ec2_runner_cloudwatch_logs" {
  name = "CloudWatchLogsAccess"
  role = aws_iam_role.ec2_runner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:${module.common.aws_region}:${module.common.aws_account_id}:log-group:/github-runner/diag:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = ["*"]
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "GitHubRunner/EC2"
          }
        }
      }
    ]
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
  name = local.lambda_role_name

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
    Name = local.lambda_role_name
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
        module.common.ssm_github_pat_arn,
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

resource "aws_iam_role_policy" "sqs_access" {
  name = "SQSAccess"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = [aws_sqs_queue.main.arn]
    }]
  })
}
