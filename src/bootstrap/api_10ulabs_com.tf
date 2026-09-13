removed {
  from = aws_iam_role.api_deploy

  lifecycle {
    destroy = false
  }
}

removed {
  from = aws_iam_role_policy.api_state

  lifecycle {
    destroy = false
  }
}

removed {
  from = aws_iam_role_policy.api_self

  lifecycle {
    destroy = false
  }
}
