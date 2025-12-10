resource "aws_iam_role" "lambda_health_handler" {
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

resource "aws_iam_role_policy_attachment" "lambda_health_handler_basic" {
  role       = aws_iam_role.lambda_health_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_health_handler_ec2_describe" {
  name = "EC2DescribePermissions"
  role = aws_iam_role.lambda_health_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_health_handler_kms" {
  name = "KMSDecryptPermissions"
  role = aws_iam_role.lambda_health_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = local.kms_lambda_alias
    }]
  })
}
