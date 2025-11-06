#!/bin/bash
set -e

# Configure GitHub repository webhook for self-hosted runners
#
# This script:
# 1. Gets webhook URL from CloudFormation stack
# 2. Gets webhook secret from Secrets Manager
# 3. Configures GitHub repository webhook to trigger runner launches
#
# Run after infrastructure is deployed to enable webhook-triggered runners.

STACK_NAME="GitHubRunnersWebhook"
SECRET_NAME="github-webhook-secret"
REGION="us-east-1"
REPO="10U-Foundation/10uf.org"

echo "==================================="
echo "GitHub Webhook Configuration"
echo "==================================="
echo ""

# Get webhook URL from CloudFormation
echo "Getting webhook URL from CloudFormation stack..."
WEBHOOK_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue' \
  --output text)

if [ -z "$WEBHOOK_URL" ]; then
  echo "ERROR: Could not get webhook URL from stack $STACK_NAME"
  exit 1
fi

echo "✓ Webhook URL: $WEBHOOK_URL"
echo ""

# Get webhook secret from Secrets Manager
echo "Getting webhook secret from Secrets Manager..."
WEBHOOK_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id $SECRET_NAME \
  --region $REGION \
  --query 'SecretString' \
  --output text)

if [ -z "$WEBHOOK_SECRET" ]; then
  echo "ERROR: Could not get webhook secret from Secrets Manager"
  exit 1
fi

echo "✓ Webhook secret retrieved"
echo ""

# Configure GitHub webhook
echo "Configuring GitHub repository webhook..."
gh api /repos/$REPO/hooks \
  -X POST \
  -f name='web' \
  -F active=true \
  -F config[url]="$WEBHOOK_URL" \
  -F config[content_type]='application/json' \
  -F config[secret]="$WEBHOOK_SECRET" \
  -F config[insecure_ssl]='0' \
  -f events[]='workflow_job' \
  --jq '.id' > /tmp/webhook_id.txt

WEBHOOK_ID=$(cat /tmp/webhook_id.txt)

echo "✓ Webhook configured!"
echo "  Webhook ID: $WEBHOOK_ID"
echo "  URL: $WEBHOOK_URL"
echo "  Event: workflow_job"
echo ""
echo "==================================="
echo "Self-hosted runners enabled!"
echo "==================================="
echo ""
echo "Jobs with labels will now trigger ephemeral runners:"
echo "  - 'ephemeral-ec2-spot-instance' → EC2 spot instances"
echo "  - 'ephemeral-ecs-fargate-spot' → Fargate spot tasks"
echo ""
echo "Example workflow:"
echo "  runs-on: [self-hosted, docker-builder, ephemeral-ec2-spot-instance]"
