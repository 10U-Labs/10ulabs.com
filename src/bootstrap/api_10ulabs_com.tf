locals {
  api_repository = "${local.github_org}@240548037/api.10ulabs.com@1368777392"
  api_subject    = "repo:${local.api_repository}:ref:refs/heads/main"
  api_role_arn   = "arn:aws:iam::${local.aws_account_id}:role/${local.name_for_api_role}"
}

data "aws_iam_policy_document" "api_trust" {
  statement {
    sid     = "GitHubActionsOnMain"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.github_oidc.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.api_subject]
    }
  }
}

data "aws_iam_policy_document" "api_state" {
  statement {
    sid       = "ListTheStateBucket"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.terraform_state.arn]
  }

  statement {
    sid       = "ReadWriteAndLockThisRepositoryState"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.terraform_state.arn}/api.10ulabs.com/*"]
  }
}

data "aws_iam_policy_document" "api_self" {
  statement {
    sid = "ReconcileThisRole"
    actions = [
      "iam:GetRole",
      "iam:UpdateRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:ListRolePolicies",
      "iam:GetRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:DetachRolePolicy",
      "iam:ListInstanceProfilesForRole",
      "iam:TagRole",
      "iam:UntagRole",
    ]
    resources = [local.api_role_arn]
  }

  statement {
    sid       = "ReadTheGitHubProvider"
    actions   = ["iam:GetOpenIDConnectProvider"]
    resources = [module.github_oidc.oidc_provider_arn]
  }
}

resource "aws_iam_role" "api_deploy" {
  name                 = local.name_for_api_role
  description          = "The role every workflow of 10U-Labs/api.10ulabs.com assumes: born here with its state and itself in reach, narrowed to its stacks by its own src/api/common/identity."
  assume_role_policy   = data.aws_iam_policy_document.api_trust.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "api_state" {
  name   = "State"
  role   = aws_iam_role.api_deploy.id
  policy = data.aws_iam_policy_document.api_state.json
}

resource "aws_iam_role_policy" "api_self" {
  name   = "Self"
  role   = aws_iam_role.api_deploy.id
  policy = data.aws_iam_policy_document.api_self.json
}
