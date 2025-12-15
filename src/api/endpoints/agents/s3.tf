# S3 Bucket for Agent Prompts
#
# Prompts are stored in S3 and fetched at runtime.
# Adding a new agent = uploading a new .md file (no redeploy needed).

resource "aws_s3_bucket" "prompts" {
  bucket = "${local.resource_prefix}-agent-prompts"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-agent-prompts"
  })
}

resource "aws_s3_bucket_versioning" "prompts" {
  bucket = aws_s3_bucket.prompts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "prompts" {
  bucket = aws_s3_bucket.prompts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "prompts" {
  bucket = aws_s3_bucket.prompts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload initial prompts from local directory
resource "aws_s3_object" "prompts" {
  for_each = fileset("${path.module}/prompts", "*.md")

  bucket       = aws_s3_bucket.prompts.id
  key          = "prompts/${each.value}"
  source       = "${path.module}/prompts/${each.value}"
  etag         = filemd5("${path.module}/prompts/${each.value}")
  content_type = "text/markdown"

  tags = local.common_tags
}
