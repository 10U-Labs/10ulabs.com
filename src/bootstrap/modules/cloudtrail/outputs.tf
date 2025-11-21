output "trail_name" {
  value = aws_cloudtrail.main.name
}

output "trail_arn" {
  value = aws_cloudtrail.main.arn
}

output "bucket_name" {
  value = aws_s3_bucket.cloudtrail.id
}

output "bucket_arn" {
  value = aws_s3_bucket.cloudtrail.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.cloudtrail.name
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.cloudtrail.arn
}
