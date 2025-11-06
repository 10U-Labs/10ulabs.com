#!/bin/bash
set -e

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --runner-version)
      RUNNER_VERSION="$2"
      shift 2
      ;;
    --runner-arch)
      RUNNER_ARCH="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Installing GitHub Actions runner version ${RUNNER_VERSION} for ${RUNNER_ARCH}..."

# Create directory with proper permissions
sudo mkdir -p /home/github-runner/actions-runner

# Download to /tmp, extract to destination, then set ownership
cd /tmp
curl -s -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz
sudo tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -C /home/github-runner/actions-runner
rm actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz

# Set ownership to github-runner
sudo chown -R github-runner:github-runner /home/github-runner

echo "GitHub Actions runner installed successfully"
