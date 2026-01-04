resource "aws_backup_vault" "sessions" {
  name = "${local.resource_prefix}-sessions-backup"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-backup"
  })
}

resource "aws_backup_plan" "sessions" {
  name = "${local.resource_prefix}-sessions-backup"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.sessions.name
    schedule          = "cron(0 5 * * ? *)"

    lifecycle {
      delete_after = 30
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-sessions-backup"
  })
}

resource "aws_iam_role" "backup" {
  name = "${local.resource_prefix}-SessionsBackup-Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "backup.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SessionsBackup-Role"
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restores" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

resource "aws_backup_selection" "sessions" {
  name         = "${local.resource_prefix}-sessions-tables"
  plan_id      = aws_backup_plan.sessions.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    aws_dynamodb_table.events.arn
  ]
}
