resource "aws_iam_role" "wan_synthesizer_github_actions" {
  name = "${local.resource_prefix}WanSynthesizerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Federated = module.github_oidc.oidc_provider_arn }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = [
              "repo:${local.github_org}/wan-synthesizer:*",
              "repo:${local.github_org}@240548037/wan-synthesizer@1262350676:*",
            ]
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "wan_synthesizer_admin" {
  role       = aws_iam_role.wan_synthesizer_github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
