output "lambda_function_name" {
  description = "Name of the runners router Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "lambda_function_arn" {
  description = "ARN of the runners router Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "sqs_queue_url" {
  description = "URL of the runners SQS queue"
  value       = aws_sqs_queue.main.url
}

output "sqs_queue_arn" {
  description = "ARN of the runners SQS queue"
  value       = aws_sqs_queue.main.arn
}

output "sqs_dlq_name" {
  description = "Name of the runners DLQ"
  value       = aws_sqs_queue.dlq.name
}

output "sqs_dlq_arn" {
  description = "ARN of the runners DLQ"
  value       = aws_sqs_queue.dlq.arn
}
