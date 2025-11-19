# AWS GitHub Actions OIDC Authentication

This AWS CDK project establishes secure OIDC (OpenID Connect) authentication between AWS and GitHub Actions, enabling GitHub workflows to assume AWS IAM roles without storing long-term credentials.

## Overview

The project creates:
- **GitHub OIDC Provider** in AWS IAM for token.actions.githubusercontent.com
- **IAM Role** that GitHub Actions can assume using web identity tokens
- **SSM Parameter** for storing GitHub Personal Access Token
- **Lambda Functions** with custom resources for infrastructure management

This eliminates the need to store `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in GitHub Secrets after initial setup.

## Architecture

```
GitHub Actions Workflow
    ↓ (OIDC Token)
AWS OIDC Provider
    ↓ (AssumeRoleWithWebIdentity)
IAM Role (GitHubActionsRole)
    ↓ (AdministratorAccess)
AWS Services
```

The CDK stack uses Lambda-backed custom resources to manage:
1. OIDC Provider creation/configuration
2. IAM Role creation with proper trust policy
3. Policy attachment and trust relationship setup

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.14+ and pip
- Node.js and npm (for CDK CLI)
- GitHub repository with Actions enabled
- AWS account with sufficient IAM permissions

## Initial Setup

### 1. AWS Preparation

Create an IAM user with `AdministratorAccess` policy:
```bash
# Visit: https://console.aws.amazon.com/iam/home#/users
# Create user, attach AdministratorAccess policy, generate access keys
```

### 2. GitHub Personal Access Token

Create a Classic PAT with required scopes:
```bash
# Visit: https://github.com/settings/tokens
# Required scopes: admin:org, repo
```

### 3. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:
```bash
# Visit: https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
GH_RUNNER_PAT=<your-github-pat>
```

### 4. Configuration

Update `config.json` with your specific values:
```json
{
  "aws": {
    "account_id": "YOUR_ACCOUNT_ID",
    "region": "us-east-1",
    "iam_role_name": "GitHubActionsRole"
  },
  "github": {
    "org": "YOUR_GITHUB_ORG",
    "repo": "YOUR_REPOSITORY_NAME"
  }
}
```

## Installation

### Local Development
```bash
# Clone and navigate to project directory
cd auth_between_aws_and_github

# Install Python dependencies
pip install -r requirements.txt

# Install CDK CLI (if not already installed)
npm install -g aws-cdk

# Deploy infrastructure
cdk deploy --require-approval never -c github_token=YOUR_GITHUB_PAT
```

### GitHub Actions Deployment
1. Commit your configuration changes
2. Push to trigger the deployment workflow
3. Monitor the Actions tab for deployment status

## Usage

### In GitHub Actions Workflows

After deployment, configure your workflows to use OIDC authentication:

```yaml
name: AWS Deployment
on: [push]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Test AWS Access
        run: aws sts get-caller-identity
```

### CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Show differences between deployed and local
cdk diff

# Deploy changes
cdk deploy

# Destroy infrastructure (manual only)
cdk destroy
```

## Configuration Reference

### AWS Section
- `account_id`: Your AWS account ID (12 digits)
- `region`: AWS region for deployment
- `iam_role_name`: Name for the GitHub Actions IAM role
- `bedrock`: Configuration for AWS Bedrock (if used)
- `secrets_manager.github_pat_secret_name`: SSM parameter name for GitHub PAT

### GitHub Section
- `org`: GitHub organization name
- `repo`: Repository name

## Security Features

- **OIDC Trust Policy**: Restricts role assumption to specific GitHub repository
- **Audience Validation**: Ensures tokens are intended for AWS STS
- **Subject Matching**: Validates GitHub repository context
- **Temporary Credentials**: No long-term AWS credentials in GitHub

## Testing

The project includes comprehensive test coverage:

```bash
# Run unit tests
pytest test/auth_between_aws_and_github/test_unit.py -v

# Run integration tests (requires deployed infrastructure)
pytest test/auth_between_aws_and_github/test_integration.py -v

# Run end-to-end tests (requires GitHub Actions environment)
pytest test/auth_between_aws_and_github/test_e2e.py -v
```

### Test Categories

- **Unit Tests**: CDK construct validation and configuration testing
- **Integration Tests**: Deployed resource verification in AWS
- **E2E Tests**: Complete OIDC workflow validation from GitHub Actions

## Troubleshooting

### Common Issues

1. **OIDC Provider Already Exists**
   - The Lambda function handles existing providers gracefully
   - Check AWS IAM console for existing OIDC providers

2. **Role Assumption Failures**
   - Verify GitHub repository matches configuration
   - Check IAM role trust policy conditions
   - Ensure `id-token: write` permission in workflow

3. **Deployment Failures**
   - Verify AWS credentials have sufficient permissions
   - Check CloudFormation stack events for detailed errors
   - Ensure GitHub PAT has required scopes

### Verification Commands

```bash
# Check OIDC provider
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com

# Check IAM role
aws iam get-role --role-name GitHubActionsRole

# Test role assumption (from GitHub Actions)
aws sts get-caller-identity
```

## Infrastructure Management

- **Cold Start**: Initial deployment requires AWS credentials and GitHub PAT
- **Warm State**: Subsequent deployments use OIDC authentication
- **Updates**: CDK automatically handles infrastructure updates
- **Rollback**: Use CloudFormation console for manual rollbacks

## File Structure

```
auth_between_aws_and_github/
├── app.py                 # CDK app entry point
├── stack.py              # Main CDK stack definition
├── config.json           # Configuration file
├── cdk.json             # CDK project configuration
├── requirements.txt      # Python dependencies
└── test/                # Test suite
    ├── test_unit.py     # Unit tests
    ├── test_integration.py # Integration tests
    └── test_e2e.py      # End-to-end tests
```
