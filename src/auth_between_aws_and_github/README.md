# AWS-GitHub Authentication Infrastructure

A self-contained Python script that manages AWS-GitHub authentication infrastructure for GitHub Actions workflows. Built with **zero external dependencies** - uses only Python standard library for maximum portability and security.

## Overview

This script automates the setup and management of AWS-GitHub OIDC authentication, enabling GitHub Actions workflows to securely access AWS resources without storing long-term credentials. The implementation uses **pure Python stdlib** with custom AWS API clients - no AWS CLI, boto3, or pip packages required.

### Key Features

- **🔒 Zero Dependencies**: Pure Python stdlib implementation - no external packages
- **🚀 Self-Contained**: Single executable script with built-in AWS API clients
- **🔄 State-Aware**: Intelligent detection of existing infrastructure
- **🤖 AI-Powered**: Bedrock integration for documentation automation
- **🛡️ Security-First**: OIDC-based authentication with automatic credential cleanup

## Requirements

- **Python 3.11+** (standard library only)
- **No AWS CLI required** - uses pure Python stdlib
- AWS account with appropriate permissions
- GitHub repository with Actions enabled

**No external dependencies, pip install, or requirements.txt needed.**

## Architecture

The script operates in three distinct states:

### COLD State
- **Condition**: No existing AWS infrastructure
- **Authentication**: Direct AWS credentials (Access Key + Secret)
- **Actions**: Creates OIDC provider, IAM role, and stores GitHub PAT
- **Transition**: Moves to WARM state after successful setup

### WARM State
- **Condition**: Infrastructure exists and operational
- **Authentication**: OIDC tokens (no long-term credentials needed)
- **Actions**: Uses existing infrastructure, retrieves secrets from AWS
- **Benefit**: Pure OIDC automation without human credentials

### DESTROY State
- **Condition**: Cleanup mode
- **Authentication**: OIDC (if available) or direct credentials
- **Actions**: Removes all created AWS resources
- **Result**: Returns to COLD state

## Usage

### Initial Setup (COLD → WARM)

```bash
python auth_between_aws_and_github.py create \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-access-key-id AKIA... \
  --aws-secret-access-key ... \
  --aws-iam-role-name GitHubActionsRole \
  --github-org your-org \
  --github-repo your-repo \
  --github-token ghp_... \
  --github-pat-secret-name github-runner-credentials \
  --bedrock-model-id us.anthropic.claude-haiku-4-5-20251001-v1:0
```

### Infrastructure Cleanup

```bash
python auth_between_aws_and_github.py destroy \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-access-key-id AKIA... \
  --aws-secret-access-key ... \
  --aws-iam-role-name GitHubActionsRole \
  --github-org your-org \
  --github-repo your-repo \
  --github-pat-secret-name github-runner-credentials
```

### README Management

```bash
# Check if README needs update
python auth_between_aws_and_github.py readme \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsRole \
  --check

# Update README content
python auth_between_aws_and_github.py readme \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsRole \
  --update
```

## Configuration

### Required AWS Permissions

The script requires AWS credentials with the following permissions:

- **IAM**: Full access for OIDC provider and role management
- **STS**: AssumeRole capabilities
- **Secrets Manager**: Create, read, update, delete secrets
- **Bedrock**: Model access for AI features

**Recommended**: Use `AdministratorAccess` policy during initial setup.

### GitHub Requirements

- **Repository**: Must have GitHub Actions enabled
- **PAT Scopes**: Classic Personal Access Token with:
  - `admin:org` - For runner registration
  - `repo` - For managing repository secrets

### Environment Detection

The script automatically detects its execution environment:

- **GitHub Actions**: Uses OIDC tokens when available
- **Local Execution**: Falls back to direct credential authentication
- **State Detection**: Automatically determines COLD/WARM state

## Implementation Details

### Pure Python stdlib Architecture

This script implements a complete AWS API client library using only Python standard library components:

- **HTTP Requests**: `urllib.request` for all API calls
- **Authentication**: Custom AWS Signature Version 4 implementation
- **JSON/XML Parsing**: Built-in `json` and `xml.etree.ElementTree`
- **Cryptography**: `hmac` and `hashlib` for request signing
- **No External Dependencies**: Zero pip packages or requirements.txt

### AWS Service Clients

Custom implementations for:

- **STS Client**: AssumeRoleWithWebIdentity, GetCallerIdentity
- **IAM Client**: OIDC provider and role management
- **Secrets Manager Client**: Secure credential storage
- **Bedrock Client**: AI model integration with auto-provisioning

### Error Handling

- **Retry Logic**: Exponential backoff for transient failures
- **HTTP Error Wrapping**: Detailed error messages with response context
- **State Recovery**: Graceful handling of partial infrastructure states
- **Network Resilience**: Timeout handling and connection management

## Security Considerations

### Credential Management

- **Temporary Credentials**: OIDC tokens expire automatically
- **Secret Rotation**: GitHub PAT stored securely in AWS Secrets Manager
- **Least Privilege**: IAM roles follow principle of minimal permissions
- **Audit Trail**: All AWS API calls logged with CloudTrail integration

### OIDC Trust Relationship

The trust policy restricts access to specific repository contexts:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:*"
      }
    }
  }]
}
```

### Bedrock Model Access

- **Anthropic Models**: Automatic access provisioning with compliance forms
- **Non-Anthropic Models**: Available by default in most regions
- **Usage Monitoring**: Built-in token limits and cost controls

## Troubleshooting

### Common Issues

#### AWS Authentication Errors
```
Error: STS access denied
Solution: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

#### GitHub PAT Validation
```
Error: GitHub PAT missing required scopes
Solution: Create new PAT with admin:org and repo scopes
```

#### OIDC Role Assumption
```
Error: Failed to assume role with OIDC
Solution: Check trust policy and GitHub Actions id-token permissions
```

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
python auth_between_aws_and_github.py create --verbose [other-args]
```

### State Recovery

If infrastructure creation is interrupted:

1. **Check current state**: Script auto-detects existing resources
2. **Resume setup**: Re-run create command (idempotent operations)
3. **Manual cleanup**: Use destroy command if needed

### Bedrock Access Issues

```
Error: AWS account not authorized for Bedrock
Solution: Create AWS support case for Bedrock model access
URL: https://console.aws.amazon.com/support/home
```

## Examples

### GitHub Actions Workflow

```yaml
name: AWS Infrastructure Setup
on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup AWS-GitHub Authentication
        run: |
          python auth_between_aws_and_github.py create \
            --aws-account-id ${{ secrets.AWS_ACCOUNT_ID }} \
            --aws-region us-east-1 \
            --aws-access-key-id ${{ secrets.AWS_ACCESS_KEY_ID }} \
            --aws-secret-access-key ${{ secrets.AWS_SECRET_ACCESS_KEY }} \
            --aws-iam-role-name GitHubActionsRole \
            --github-org ${{ github.repository_owner }} \
            --github-repo ${{ github.event.repository.name }} \
            --github-token ${{ secrets.GH_RUNNER_PAT }} \
            --github-pat-secret-name github-runner-credentials \
            --bedrock-model-id us.anthropic.claude-haiku-4-5-20251001-v1:0
```

### Local Development

```bash
# Export credentials
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export GH_RUNNER_PAT=ghp_...

# Run setup
python auth_between_aws_and_github.py create \
  --aws-account-id $(aws sts get-caller-identity --query Account --output text) \
  --aws-region us-east-1 \
  --aws-access-key-id $AWS_ACCESS_KEY_ID \
  --aws-secret-access-key $AWS_SECRET_ACCESS_KEY \
  --aws-iam-role-name GitHubActionsRole \
  --github-org your-org \
  --github-repo your-repo \
  --github-token $GH_RUNNER_PAT \
  --github-pat-secret-name github-runner-credentials \
  --bedrock-model-id us.anthropic.claude-haiku-4-5-20251001-v1:0
```