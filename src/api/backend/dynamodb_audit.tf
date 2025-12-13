# DynamoDB table for API request audit logging
# Used by all endpoints for durability and audit trails

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

  # GSI1: Query by endpoint and time
  global_secondary_index {
    name            = "endpoint-time-index"
    hash_key        = "endpoint"
    range_key       = "request_timestamp"
    projection_type = "ALL"
  }

  # GSI2: Find orphaned requests (status=processing)
  global_secondary_index {
    name            = "status-time-index"
    hash_key        = "status"
    range_key       = "request_timestamp"
    projection_type = "ALL"
  }

  # Auto-delete records after 90 days
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
