import {
  id = "HealthHandler-ServiceRole"
  to = aws_iam_role.lambda_health_handler
}

import {
  id = "/aws/lambda/TenULabsHealthHandler"
  to = aws_cloudwatch_log_group.health_handler
}

import {
  id = "TenULabsHealthHandler"
  to = aws_lambda_function.health_handler
}
