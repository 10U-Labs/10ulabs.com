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

resource "aws_iam_role_policy" "ecr_access" {
  name = "ECRAccess"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchDeleteImage",
          "ecr:BatchGetImage",
          "ecr:DescribeImages",
          "ecr:GetRepositoryPolicy",
          "ecr:ListImages",
          "ecr:PutImage"
        ]
        Resource = [local.ecr_repository_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "ssm_access" {
  name = "SSMAccess"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [module.shared.ssm_github_pat_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "kms_access" {
  name = "KMSDecryptPermissions"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = module.shared.kms_lambda_key_arn
    }]
  })
}
