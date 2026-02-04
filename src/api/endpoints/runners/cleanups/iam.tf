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
      Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
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

resource "aws_iam_role_policy" "ecs_access" {
  name = "ECSAccess"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecs:StopTask"
      ]
      Resource = ["*"]
      Condition = {
        ArnEquals = {
          "ecs:cluster" = data.terraform_remote_state.runners_ecs.outputs.cluster_arn
        }
      }
      }, {
      Effect = "Allow"
      Action = [
        "ecs:ListTasks"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "ec2_access" {
  name = "EC2Access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:DescribeInstances",
        "ec2:TerminateInstances"
      ]
      Resource = ["*"]
    }]
  })
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "scheduler" {
  name = "${local.resource_prefix}RunnersCleanupSchedulerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}RunnersCleanupSchedulerRole"
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "InvokeLambda"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.handler.arn
    }]
  })
}
