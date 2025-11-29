resource "aws_dynamodb_table" "configurations" {
  name         = "${local.resource_prefix}-rack-designer-configurations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "config_hash"

  attribute {
    name = "config_hash"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-rack-designer-configurations"
  })
}
