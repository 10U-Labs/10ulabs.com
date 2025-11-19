# AWS-GitHub OIDC Authentication Infrastructure

A comprehensive AWS CDK project that establishes secure OpenID Connect (OIDC) authentication between GitHub Actions and AWS, enabling GitHub workflows to assume AWS IAM roles without storing long-term credentials.

## Overview

This infrastructure project automates the setup of:
- **GitHub OIDC Provider** in AWS IAM
- **IAM Role** with trust policy for GitHub Actions
- **SSM Parameter** for GitHub Personal Access Token storage
- **Lambda Functions** for resource management via CloudFormation Custom Resources

The solution enables GitHub Actions workflows to authenticate with AWS using short-lived OIDC tokens, following AWS security best practices.

## Architecture

```
GitHub Actions → OIDC Token → AWS STS AssumeRoleWithWebIdentity → IAM Role → AWS Services
```

### Components

1. **OIDC Provider**: Establishes trust between GitHub and AWS
2. **IAM Role**: `GitHubActionsRole` with AdministratorAccess permissions
3. **Lambda Functions**: Custom resource handlers for OIDC provider and IAM role management
4. **SSM Parameter**: Secure storage for GitHub Personal Access Token
5. **Trust Policy**: Restricts role assumption to specific GitHub repository

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.8+ and pip
- Node.js (for AWS CDK)
- GitHub repository with Actions enabled
- AWS account with AdministratorAccess permissions

## Quick Start

### Initial Setup (Cold Start)

For first-time deployment, you need AWS credentials and GitHub PAT:

1. **Create AWS IAM User**
   - Go to [AWS IAM Console](https://console.aws.amazon.com/iam/home#/users)
   - Create user with `AdministratorAccess` policy
   - Generate access key and save credentials

2. **Create GitHub Personal Access Token**
   - Go to [GitHub Tokens](https://github.com/settings/tokens)
   - Create Classic token with scopes: `admin:org`, `repo`

3. **Configure GitHub Secrets**
   - Add to repository secrets:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `GH_RUNNER_PAT`

4. **Deploy Infrastructure**
   ```bash
   cd auth_between_aws_and_github
   pip install -r requirements.txt
   cdk deploy --require-approval never
   ```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Deploy with GitHub token
cdk deploy --require-approval never -c github_token=YOUR_GITHUB_PAT

# View differences before deployment
cdk diff

# Destroy infrastructure (manual only)
cdk destroy
```

## Configuration

The `config.json` file contains all infrastructure settings:

```json
{
  "aws": {
    "account_id": "781581267945",
    "region": "us-east-1",
    "iam_role_name": "GitHubActionsRole"
  },
  "github": {
    "org": "10U-Labs-LLC",
    "repo": "10ulabs.com"
  }
}
```

### Key Configuration Options

- **AWS Account**: Target AWS account for resource deployment
- **Region**: AWS region for resource creation
- **IAM Role Name**: Name of the role GitHub Actions will assume
- **GitHub Org/Repo**: Repository allowed to assume the IAM role
- **Bedrock Settings**: Token limits and model configuration for AI services

## Usage

### In GitHub Actions Workflows

```yaml
name: Deploy Infrastructure
on: [push]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::781581267945:role/GitHubActionsRole
          aws-region: us-east-1
          
      - name: Deploy with CDK
        run: |
          npm install -g aws-cdk
          pip install -r requirements.txt
          cdk deploy --require-approval never
```

### Security Features

- **Repository Scoped**: Role can only be assumed by specified GitHub repository
- **OIDC Token Validation**: AWS validates GitHub's OIDC token claims
- **Audience Restriction**: Only `sts.amazonaws.com` audience accepted
- **Subject Pattern**: Restricts to `repo:ORG/REPO:*` pattern

## Testing

Comprehensive test suite covering multiple levels:

```bash
# Install test dependencies
pip install pytest boto3-stubs

# Run all tests
pytest test/

# Run specific test categories
pytest test/test_unit.py          # Unit tests
pytest test/test_integration.py   # Integration tests  
pytest test/test_e2e.py          # End-to-end tests
```

### Test Categories

- **Unit Tests**: CDK construct validation and configuration testing
- **Integration Tests**: Deployed AWS resource verification
- **End-to-End Tests**: Complete OIDC workflow validation

## Infrastructure Management

### Deployment States

- **Cold Start**: Initial deployment requires AWS credentials + GitHub PAT
- **Warm State**: Subsequent deployments use OIDC authentication
- **Updates**: CDK automatically handles resource updates
- **Rollback**: Use CloudFormation console for manual rollbacks

### Monitoring

The infrastructure creates the following resources:
- CloudFormation Stack: `AuthBetweenAwsAndGithub`
- IAM OIDC Provider: `token.actions.githubusercontent.com`
- IAM Role: `GitHubActionsRole`
- SSM Parameter: `/github-runner/credentials`
- Lambda Functions: OIDC and IAM role management

### Troubleshooting

#### Common Issues

1. **OIDC Token Validation Failed**
   - Verify repository name in config matches actual repository
   - Check GitHub Actions has `id-token: write` permission

2. **Role Assumption Failed**
   - Confirm OIDC provider thumbprint is current
   - Validate trust policy conditions

3. **Deployment Failures**
   - Check AWS credentials have sufficient permissions
   - Verify CDK version compatibility

#### Debug Commands

```bash
# Check current AWS identity
aws sts get-caller-identity

# Validate CDK synthesis
cdk synth

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name AuthBetweenAwsAndGithub
```

## Development

### Project Structure

```
├── app.py              # CDK app entry point
├── stack.py            # Main CDK stack definition
├── config.json         # Infrastructure configuration
├── requirements.txt    # Python dependencies
├── cdk.json           # CDK configuration
└── test/              # Test suite
    ├── test_unit.py
    ├── test_integration.py
    └── test_e2e.py
```

### Adding New Resources

1. Update `stack.py` with new CDK constructs
2. Add configuration options to `config.json`
3. Update tests in appropriate test files
4. Deploy and validate changes

## Security Considerations

- IAM role has AdministratorAccess (adjust based on actual needs)
- OIDC provider uses GitHub's current thumbprint
- Trust policy restricts access to specific repository
- GitHub PAT stored securely in SSM Parameter Store
- All infrastructure deployed via CloudFormation for audit trail
