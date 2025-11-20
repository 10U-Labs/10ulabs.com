#!/bin/bash
set -e

JOB_ID="${JOB_ID:-unknown}"
RUNNER_LABELS="${RUNNER_LABELS:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="${GITHUB_REPO:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "=== Ephemeral EC2 Spot Runner Setup ==="
echo "Job ID: ${JOB_ID}"
echo "Labels: ${RUNNER_LABELS}"

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
    echo "ERROR: GITHUB_TOKEN and GITHUB_REPO required"
    shutdown -h now
    exit 1
fi

echo "Getting registration token..."
RUNNER_TOKEN=$(curl -L \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token" \
    2>/dev/null | jq -r '.token')

if [ -z "$RUNNER_TOKEN" ] || [ "$RUNNER_TOKEN" = "null" ]; then
    echo "ERROR: Failed to get runner token"
    shutdown -h now
    exit 1
fi

echo "Got registration token, registering runner..."

RUNNER_DIR="/home/github-runner/actions-runner"
HOSTNAME=$(hostname)
RUNNER_NAME="ec2-spot-${HOSTNAME}"

cd "$RUNNER_DIR"

echo "Running config.sh..."
sudo -u github-runner ./config.sh \
    --url "https://github.com/${GITHUB_REPO}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --ephemeral \
    --unattended

if [ ! -f "${RUNNER_DIR}/.runner" ]; then
    echo "ERROR: Runner registration failed - .runner file not created"
    echo "Directory contents:"
    ls -la "$RUNNER_DIR"
    shutdown -h now
    exit 1
fi

echo "Runner registered successfully, starting job execution..."

sudo -u github-runner ./run.sh

echo "Job completed, self-terminating..."

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$AWS_REGION" \
    || shutdown -h now
