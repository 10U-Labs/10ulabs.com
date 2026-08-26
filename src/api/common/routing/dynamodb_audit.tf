resource "aws_dynamodb_table" "api_audit_log" {
  name         = "${local.resource_prefix}ApiAuditLog"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  range_key    = "endpoint_timestamp"

  attribute {
    name = "request_id"
    type = "S"
  }

  attribute {
    name = "endpoint_timestamp"
    type = "S"
  }

  attribute {
    name = "endpoint"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "request_timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "endpoint-time-index"
    hash_key        = "endpoint"
    range_key       = "request_timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "status-time-index"
    hash_key        = "status"
    range_key       = "request_timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}ApiAuditLog"
  })
}
