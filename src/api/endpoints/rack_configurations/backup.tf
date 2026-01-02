resource "aws_backup_vault" "rack_designer" {
  name = "${local.resource_prefix}-rack-configurations-backup"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-configurations-backup"
  })
}

resource "aws_backup_plan" "rack_designer" {
  name = "${local.resource_prefix}-rack-configurations-backup"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.rack_designer.name
    schedule          = "cron(0 5 * * ? *)"

    lifecycle {
      delete_after = 30
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-configurations-backup"
  })
}

resource "aws_iam_role" "backup" {
  name = "${local.resource_prefix}-RackConfigurationsBackup-Role"

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
    Name = "${local.resource_prefix}-RackConfigurationsBackup-Role"
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

resource "aws_backup_selection" "rack_designer" {
  name         = "${local.resource_prefix}-rack-configurations-tables"
  plan_id      = aws_backup_plan.rack_designer.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    aws_dynamodb_table.configurations.arn,
    aws_dynamodb_table.events.arn
  ]
}
