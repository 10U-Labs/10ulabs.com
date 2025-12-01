resource "aws_dynamodb_table" "idempotency" {
  name         = var.idempotency_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = var.idempotency_table_name
  })
}

resource "aws_dynamodb_table" "incidents" {
  name         = "${local.resource_prefix}-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-incidents"
  })
}

resource "aws_dynamodb_table" "circuit_breaker_state" {
  name             = "${local.resource_prefix}-circuit-breaker-state"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "state_id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "state_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-state"
  })
}

resource "aws_dynamodb_table" "workflow_runners" {
  name         = "${local.resource_prefix}-workflow-runners"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_id"
  range_key    = "runner_type"

  attribute {
    name = "run_id"
    type = "S"
  }

  attribute {
    name = "runner_type"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-workflow-runners"
  })
}
