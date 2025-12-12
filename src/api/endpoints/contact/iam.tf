resource "aws_iam_role" "lambda_contact_handler" {
  name = local.contact_handler_role_name

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
    Name = local.contact_handler_role_name
  })
}

resource "aws_iam_role_policy_attachment" "lambda_contact_handler_basic" {
  role       = aws_iam_role.lambda_contact_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_contact_handler_ssm" {
  name = "SSMParameterAccess"
  role = aws_iam_role.lambda_contact_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = [aws_ssm_parameter.recaptcha_secret.arn]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_contact_handler_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.lambda_contact_handler.id

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

resource "aws_iam_role_policy" "lambda_contact_handler_ses" {
  name = "SESAccess"
  role = aws_iam_role.lambda_contact_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ses:SendEmail"]
      Resource = ["*"]
      Condition = {
        StringEquals = {
          "ses:FromAddress" = "contact@${local.domain_name}"
        }
      }
    }]
  })
}
