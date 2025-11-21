#!/bin/bash
set -e

echo "Starting Terraform resource import..."
echo "======================================"

echo "1. Importing S3 bucket..."
terraform import aws_s3_bucket.docs api.10ulabs.com

echo "2. Importing CloudFront cache policy..."
CACHE_POLICY_ID=$(aws cloudfront list-cache-policies --type custom --query "CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name=='ApiDocsCachePolicy'].CachePolicy.Id" --output text)
terraform import aws_cloudfront_cache_policy.docs "$CACHE_POLICY_ID"

echo "3. Importing ECR repository..."
terraform import aws_ecr_repository.runner github-runner

echo "4. Importing ECS cluster..."
terraform import aws_ecs_cluster.runner TenULabsRunnerCluster

echo "5. Importing IAM role for EC2 runner..."
terraform import aws_iam_role.ec2_runner_role GitHubSelfHostedRunnerEC2Role

echo "6. Importing CloudWatch log group for runners handler..."
terraform import aws_cloudwatch_log_group.runners_handler /aws/lambda/TenULabsWebhookHandler

echo "7. Importing SQS webhook DLQ..."
terraform import aws_sqs_queue.webhook_dlq https://sqs.us-east-1.amazonaws.com/781581267945/TenULabsWebhookHandler-dlq

echo "8. Importing SQS job queue DLQ..."
terraform import aws_sqs_queue.job_queue_dlq https://sqs.us-east-1.amazonaws.com/781581267945/TenULabsWebhookHandler-job-dlq

echo "9. Importing DynamoDB idempotency table..."
terraform import aws_dynamodb_table.idempotency TenULabsWebhookHandler-idempotency

echo "10. Importing SSM parameter for GitHub token..."
terraform import aws_ssm_parameter.github_token /github-runner/credentials

echo "11. Importing SSM parameter for latest AMI..."
terraform import aws_ssm_parameter.latest_ami /github-runner/ami/latest

echo "12. Importing SSM parameter for webhook secret..."
terraform import aws_ssm_parameter.webhook_secret /api-webhook-secret

echo "======================================"
echo "Import complete! Running terraform plan to verify..."
terraform plan -detailed-exitcode || echo "Note: Exit code $? - review plan output above"
