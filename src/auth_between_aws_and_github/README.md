# AWS and GitHub Actions OIDC Authentication Infrastructure

This AWS CDK infrastructure project establishes secure, passwordless
authentication between GitHub Actions and AWS using OpenID Connect (OIDC).
It eliminates the need for long-lived AWS access keys in GitHub Secrets
by enabling GitHub Actions workflows to assume AWS IAM roles directly.

## Purpose and Key Features

- **Passwordless Authentication**: GitHub Actions can authenticate to AWS
  without storing AWS credentials
- **Secure Token Exchange**: Uses OIDC tokens from GitHub Actions to assume
  AWS IAM roles
- **Automated Deployment**: Self-bootstrapping infrastructure that can be
  deployed via GitHub Actions
- **Repository-Specific Access**: IAM role is scoped to a specific GitHub
  organization and repository
- **Administrative Access**: Provides full AWS administrative access to
  GitHub Actions workflows

## Resources Created

This infrastructure creates the following AWS resources:

### IAM Resources

- **GitHub OIDC Identity Provider**: Establishes trust relationship with
  GitHub's OIDC endpoint (`token.actions.githubusercontent.com`)
- **GitHub Actions IAM Role**: IAM role that can be assumed by GitHub Actions
  workflows from the specified repository
- **Lambda Execution Roles**: IAM roles for the custom resource Lambda
  functions with appropriate permissions

### Lambda Functions

- **OIDC Provider Lambda**: Custom resource function that creates and manages
  the GitHub OIDC identity provider
- **IAM Role Lambda**: Custom resource function that creates and manages the
  GitHub Actions IAM role with proper trust policy

### Secrets Manager Integration

- **GitHub PAT Secret**: References existing Secrets Manager secret
  containing GitHub Personal Access Token for repository access

## Prerequisites and Requirements

### Python Dependencies

Install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib>=2.100.0` - AWS CDK framework
- `constructs>=10.0.0` - CDK constructs library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[iam,sts,secretsmanager,bedrock-runtime]>=1.34.0` - Type stubs
- `typeguard==2.13.3` - Runtime type checking

### System Dependencies

- **Python 3.8+**: Required for AWS CDK Python applications
- **Node.js 18+**: Required for AWS CDK toolkit
- **Git**: Required for repository operations

### AWS Setup

- AWS account with appropriate permissions to create IAM resources
- AWS credentials configured (for initial deployment only)
- AWS CDK toolkit installed: `npm install -g aws-cdk`

### GitHub Setup

- GitHub repository with Actions enabled
- GitHub Personal Access Token with `admin:org` and `repo` scopes
- GitHub Secrets configured for initial deployment

## Configuration

### config.json Structure

The `config.json` file contains all configuration parameters:

```json
{
  "aws": {
    "account_id": "781581267945",
    "region": "us-east-1",
    "iam_role_name": "GitHubActionsRole",
    "secrets_manager": {
      "github_pat_secret_name": "github-runner/credentials"
    },
    "bedrock": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000
    }
  },
  "github": {
    "org": "10U-Labs-LLC",
    "repo": "10ulabs.com"
  }
}
```

### CDK Configuration

The `cdk.json` file configures CDK behavior:

- **App Command**: `python3 app.py`
- **File Watching**: Monitors all files except documentation and cache
- **Feature Flags**: Enables latest CDK features and best practices

## Usage Instructions

### Initial Setup (First Time)

1. **Create AWS IAM User** at
   <https://console.aws.amazon.com/iam/home#/users>

   ```bash
   # Attach AdministratorAccess policy
   # Create access key and save credentials
   ```

2. **Create GitHub Classic PAT** at
   <https://github.com/settings/tokens>

   ```text
   Required scopes: admin:org, repo
   ```

3. **Add GitHub Secrets** at repository settings

   ```text
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY  
   GH_RUNNER_PAT
   ```

4. **Deploy Infrastructure**

   ```bash
   # Update config.json with your values
   git add . && git commit -m "Initial OIDC setup"
   git push origin main
   ```

### Local Deployment

For local development and testing:

```bash
# Navigate to project directory
cd auth_between_aws_and_github

# Install dependencies
pip install -r requirements.txt

# Deploy infrastructure
cdk deploy --require-approval never \
  -c github_token=YOUR_GITHUB_PAT

# View deployment diff
cdk diff

# Destroy infrastructure (manual only)
cdk destroy
```

### Using the Deployed Resources

Once deployed, GitHub Actions workflows can authenticate to AWS:

```yaml
# .github/workflows/example.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
          aws-region: us-east-1
      - run: aws sts get-caller-identity
```

## Architecture Overview

### Authentication Flow

1. **GitHub Actions Request**: Workflow requests OIDC token from GitHub
2. **Token Validation**: AWS validates token against OIDC provider
3. **Role Assumption**: GitHub Actions assumes the configured IAM role
4. **AWS API Access**: Workflow gains temporary AWS credentials

### Component Interactions

```text
GitHub Actions → OIDC Token → AWS STS → Assume Role → AWS Services
```

### Trust Relationship

The IAM role trust policy allows assumption only from:

- **Audience**: `sts.amazonaws.com`
- **Subject**: `repo:ORG/REPO:*` (specific repository)
- **Provider**: GitHub's OIDC endpoint

### Custom Resources

Two Lambda functions manage infrastructure lifecycle:

- **OIDC Provider Management**: Creates/updates GitHub OIDC provider
- **IAM Role Management**: Creates/updates GitHub Actions role with proper
  trust policy

## Security Considerations

### Access Control

- **Repository Scoping**: IAM role can only be assumed by the specified
  GitHub repository
- **Branch Protection**: Consider limiting access to specific branches
  using trust policy conditions
- **Least Privilege**: Review AdministratorAccess attachment and consider
  more restrictive policies

### Token Security

- **Short-Lived Tokens**: OIDC tokens are temporary and automatically rotate
- **No Long-Lived Secrets**: Eliminates need for permanent AWS access keys
- **Secure Token Exchange**: Uses AWS STS for secure credential exchange

### Monitoring

- **CloudTrail Integration**: All AWS API calls are logged via CloudTrail
- **Role Usage Tracking**: Monitor AssumeRoleWithWebIdentity events
- **Access Patterns**: Review unusual access patterns or locations

## Troubleshooting

### Common Issues

**"No OpenIDConnectProvider found"**

```bash
# Check if OIDC provider exists
aws iam list-open-id-connect-providers

# Re-deploy if missing
cdk deploy --require-approval never
```

**"Access denied during role assumption"**

```yaml
# Ensure workflow has correct permissions
permissions:
  id-token: write
  contents: read
```

**"Invalid repository in trust policy"**

```bash
# Verify config.json has correct org/repo values
cat config.json | jq '.github'

# Update and re-deploy
cdk deploy --require-approval never
```

### Debug Steps

1. **Verify OIDC Provider**: Check AWS IAM console for GitHub provider
2. **Check Trust Policy**: Ensure IAM role trust policy matches repository
3. **Test Locally**: Use `aws sts get-caller-identity` to verify access
4. **Review Logs**: Check CloudWatch logs for Lambda function errors
5. **Validate Token**: Ensure GitHub Actions has `id-token: write` permission

### Infrastructure Management

- **Deploy Changes**: Commit configuration updates to trigger deployment
- **View Differences**: Use `cdk diff` to preview changes
- **Manual Deployment**: Use local CDK commands for testing
- **Resource Cleanup**: Use `cdk destroy` for complete removal
