# Deploy role for the wan-graph-designer repo's GitHub Actions (GitOps).
#
# It reuses the account's shared GitHub OIDC provider (created by
# module.github_oidc) and is assumable ONLY by that repo's workflows. The repo
# provisions its own IAM/Lambda/API-Gateway/S3/ECS stacks, so it gets
# AdministratorAccess -- matching this account's own GitHubActionsRole. Set the
# output ARN as the wan-graph-designer repo's OIDC_ROLE_ARN GitHub variable.

resource "aws_iam_role" "wan_graph_designer_github_actions" {
  name = "${local.resource_prefix}WanGraphDesignerRole"

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
              "repo:${local.github_org}/wan-graph-synthesizer:*",
              "repo:${local.github_org}/wan-synthesizer:*",
              # Renaming a repository makes GitHub qualify its subject claim with ids a
              # rename cannot change, so neither plain name above matches any more. The
              # numbers are the organisation's id and the repository's, read back with
              # "gh api repos/10U-Labs/wan-synthesizer/actions/oidc/customization/sub".
              # They are written out rather than wildcarded: "@*" would also admit a
              # repository of that name in any organisation.
              "repo:${local.github_org}@240548037/wan-synthesizer@1262350676:*",
            ]
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "wan_graph_designer_admin" {
  role       = aws_iam_role.wan_graph_designer_github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
