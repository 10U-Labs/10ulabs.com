resource "aws_backup_vault" "sessions" {
  name = local.backup_vault_name

  tags = merge(local.common_tags, {
    Name = local.backup_vault_name
  })
}

resource "aws_backup_plan" "sessions" {
  name = local.backup_vault_name

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.sessions.name
    schedule          = "cron(0 5 * * ? *)"

    lifecycle {
      delete_after = 30
    }
  }

  tags = merge(local.common_tags, {
    Name = local.backup_vault_name
  })
}

resource "aws_iam_role" "backup" {
  name = local.backup_role_name

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
    Name = local.backup_role_name
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
  name         = local.backup_selection_name
  plan_id      = aws_backup_plan.sessions.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    aws_dynamodb_table.events.arn
  ]
}
