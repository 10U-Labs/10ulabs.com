# S3 bucket for archiving ignored webhook events
resource "aws_s3_bucket" "ignored_events_archive" {
  bucket = "${local.resource_prefix}-ignored-events-archive"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ignored-events-archive"
  })
}

resource "aws_s3_bucket_versioning" "ignored_events_archive" {
  bucket = aws_s3_bucket.ignored_events_archive.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ignored_events_archive" {
  bucket = aws_s3_bucket.ignored_events_archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "ignored_events_archive" {
  bucket = aws_s3_bucket.ignored_events_archive.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "ignored_events_archive" {
  bucket = aws_s3_bucket.ignored_events_archive.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    filter {
      prefix = "ignored-events/"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
