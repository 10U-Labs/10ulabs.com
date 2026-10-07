resource "aws_cloudfront_function" "spa_routing" {
  name    = local.spa_routing_function_name
  runtime = "cloudfront-js-2.0"
  comment = "SPA routing and apex-to-www redirect"
  publish = true
  code    = file("${path.module}/function/spa_routing.js")
}

removed {
  from = aws_lambda_function.spa_routing

  lifecycle {
    destroy = false
  }
}

removed {
  from = aws_iam_role.spa_routing

  lifecycle {
    destroy = false
  }
}

removed {
  from = aws_iam_role_policy_attachment.spa_routing_basic

  lifecycle {
    destroy = false
  }
}
