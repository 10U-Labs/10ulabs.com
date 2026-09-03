resource "aws_dynamodb_table" "events" {
  name         = local.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "event_type"
    type = "S"
  }

  attribute {
    name = "device_id"
    type = "S"
  }

  global_secondary_index {
    name            = "event_type-index"
    hash_key        = "event_type"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "device_id-index"
    hash_key        = "device_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = local.dynamodb_table_name
  })
}
