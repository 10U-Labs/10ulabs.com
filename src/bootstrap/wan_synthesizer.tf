removed {
  from = aws_iam_role.wan_synthesizer_github_actions

  lifecycle {
    destroy = false
  }
}

removed {
  from = aws_iam_role_policy_attachment.wan_synthesizer_admin

  lifecycle {
    destroy = false
  }
}
