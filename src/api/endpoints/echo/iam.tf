resource "aws_iam_role" "lambda_echo_handler" {
  name = "EchoHandler-ServiceRole"

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
    Name = "EchoHandler-ServiceRole"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_echo_handler_basic" {
  role       = aws_iam_role.lambda_echo_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
