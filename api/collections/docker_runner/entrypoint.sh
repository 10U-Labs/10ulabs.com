#!/bin/bash
set -e

# Check required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN is not set"
    exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
    echo "Error: GITHUB_REPO is not set"
    exit 1
fi

# Default values
RUNNER_LABELS="${RUNNER_LABELS:-fargate,general}"
RUNNER_GROUP="${RUNNER_GROUP:-default}"
RUNNER_NAME="${RUNNER_NAME:-fargate-runner-$(hostname)}"

echo "Registering GitHub Actions runner..."
echo "Repository: $GITHUB_REPO"
echo "Runner Name: $RUNNER_NAME"
echo "Labels: $RUNNER_LABELS"

# Get registration token
REGISTRATION_TOKEN=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token | jq -r .token)

if [ -z "$REGISTRATION_TOKEN" ] || [ "$REGISTRATION_TOKEN" = "null" ]; then
    echo "Error: Failed to get registration token"
    exit 1
fi

# Configure runner
./config.sh \
    --url "https://github.com/${GITHUB_REPO}" \
    --token "${REGISTRATION_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --work _work \
    --unattended \
    --ephemeral

# Cleanup function
cleanup() {
    echo "Removing runner..."
    ./config.sh remove --token "${REGISTRATION_TOKEN}"
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Start runner
echo "Starting runner..."
./run.sh &

# Wait for runner process
wait $!
