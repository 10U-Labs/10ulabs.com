#!/bin/bash
set -e

echo "Waiting for EC2 instance status checks to pass..."

# Get instance ID and region using IMDSv2
TOKEN=$(curl -s -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)

echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"

# Poll every 15 seconds for up to 5 minutes
POLL_INTERVAL=15
MAX_ATTEMPTS=20
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))
  echo "Checking status (attempt $ATTEMPT/$MAX_ATTEMPTS)..."

  # Check both instance status and system status
  STATUS_OUTPUT=$(aws ec2 describe-instance-status \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'InstanceStatuses[0].[InstanceStatus.Status,SystemStatus.Status]' \
    --output text)

  INSTANCE_STATUS=$(echo $STATUS_OUTPUT | awk '{print $1}')
  SYSTEM_STATUS=$(echo $STATUS_OUTPUT | awk '{print $2}')

  echo "  Instance Status: $INSTANCE_STATUS"
  echo "  System Status: $SYSTEM_STATUS"

  if [ "$INSTANCE_STATUS" = "ok" ] && [ "$SYSTEM_STATUS" = "ok" ]; then
    echo "All status checks passed"
    break
  fi

  if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Status checks did not pass after $MAX_ATTEMPTS attempts"
    exit 1
  fi

  # Poll every 15 seconds
  echo "  Status not ready - waiting ${POLL_INTERVAL}s before retry..."
  sleep $POLL_INTERVAL
done

echo "Instance is ready for provisioning"
