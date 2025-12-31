resource "aws_iam_role" "lambda_simulation_soc_handler" {
  name = local.handler_role_name

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
    Name = local.handler_role_name
  })
}

resource "aws_iam_role_policy_attachment" "lambda_simulation_soc_handler_basic" {
  role       = aws_iam_role.lambda_simulation_soc_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_simulation_soc_handler_kms" {
  name = "KMSDecryptPermissions"
  role = aws_iam_role.lambda_simulation_soc_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = module.common.kms_lambda_key_arn
    }]
  })
}
