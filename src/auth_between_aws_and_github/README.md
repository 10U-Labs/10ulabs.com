# AWS-GitHub OIDC Authentication Infrastructure

This AWS CDK project establishes secure OpenID Connect (OIDC) authentication
between GitHub Actions and AWS, eliminating the need for long-lived AWS
access keys in CI/CD pipelines.

## Overview

The infrastructure creates an OIDC identity provider in AWS that trusts
GitHub's token service, along with an IAM role that GitHub Actions can assume
using short-lived tokens. This enables secure, keyless authentication for
automated deployments and AWS operations from GitHub workflows.

## Key Features

- **Keyless Authentication**: No AWS access keys stored in GitHub secrets
- **Short-lived Tokens**: GitHub issues temporary tokens for each workflow run
- **Automated Setup**: CDK handles OIDC provider and IAM role creation
- **Repository-scoped Access**: IAM role restricted to specific GitHub
  repository
- **Administrator Permissions**: Full AWS access for deployment automation

## Main Components

### OIDC Provider Management

- **Custom Lambda Function**: Creates and manages GitHub OIDC provider in AWS
- **GitHub Token Service**: Configured trust relationship with
  `token.actions.githubusercontent.com`
- **SSL Thumbprint Validation**: Uses GitHub's current SSL certificate
  thumbprint

### IAM Role Creation

- **GitHub Actions Role**: IAM role assumable by GitHub workflows
- **Trust Policy**: Restricts access to specific GitHub organization and
  repository
- **Administrator Access**: Attached AWS managed policy for full permissions

### Secrets Management

- **GitHub PAT Storage**: AWS Secrets Manager integration for GitHub Personal
  Access Tokens
- **Secure Retrieval**: Encrypted storage of sensitive GitHub credentials

## Prerequisites

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages from `requirements.txt`:

- `aws-cdk-lib>=2.100.0` - AWS CDK framework
- `constructs>=10.0.0` - CDK construct library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[iam,sts,secretsmanager,bedrock-runtime]>=1.34.0` - Type hints
- `typeguard==2.13.3` - Runtime type checking

### System Dependencies

- **Python 3.11+**: Required for Lambda runtime compatibility
- **Node.js 18+**: Required for AWS CDK CLI
- **Git**: For repository operations and version control

### AWS Setup

- AWS account with appropriate permissions
- IAM user with `AdministratorAccess` policy (for initial deployment)
- AWS credentials configured (temporary, for bootstrap only)

### GitHub Setup

- GitHub repository with Actions enabled
- GitHub Personal Access Token with `admin:org` and `repo` scopes
- Repository access to GitHub Secrets

## Configuration

### config.json Structure

The configuration file defines AWS and GitHub integration parameters:

```json
{
  "aws": {
    "account_id": "781581267945",
    "region": "us-east-1",
    "iam_role_name": "GitHubActionsRole",
    "secrets_manager": {
      "github_pat_secret_name": "github-runner/credentials"
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

- **App Entry Point**: `python3 app.py`
- **File Watching**: Monitors changes excluding cache and config files
- **Feature Flags**: Modern AWS CDK best practices enabled
- **Context Settings**: Partition support for `aws` and `aws-cn`

## Installation and Deployment

### Initial Setup

1. **Clone Repository**

   ```bash
   git clone <repository-url>
   cd auth_between_aws_and_github
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   npm install -g aws-cdk
   ```

3. **Configure AWS Credentials** (temporary)

   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Update Configuration**

   Edit `config.json` with your AWS account ID and GitHub details:

   ```json
   {
     "aws": {
       "account_id": "YOUR_ACCOUNT_ID",
       "region": "YOUR_REGION"
     },
     "github": {
       "org": "YOUR_GITHUB_ORG",
       "repo": "YOUR_REPOSITORY"
     }
   }
   ```

### Deployment Commands

1. **Bootstrap CDK** (first time only)

   ```bash
   cdk bootstrap
   ```

2. **Preview Changes**

   ```bash
   cdk diff
   ```

3. **Deploy Infrastructure**

   ```bash
   cdk deploy --require-approval never
   ```

4. **Verify Deployment**

   ```bash
   aws iam get-role --role-name GitHubActionsRole
   aws iam list-open-id-connect-providers
   ```

### GitHub Actions Integration

Add the following to your GitHub workflow:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Verify AWS access
        run: aws sts get-caller-identity
```

## Architecture Overview

### Authentication Flow

1. **Workflow Trigger**: GitHub Actions workflow starts
2. **Token Request**: GitHub requests OIDC token from its token service
3. **Token Validation**: AWS validates token against OIDC provider
4. **Role Assumption**: GitHub Actions assumes IAM role using validated token
5. **AWS Operations**: Workflow executes with temporary AWS credentials

### Component Interactions

```text
GitHub Actions → GitHub Token Service → AWS OIDC Provider → IAM Role → AWS Services
```

### Security Model

- **Identity Federation**: GitHub acts as trusted identity provider
- **Conditional Access**: IAM policies restrict access to specific repository
- **Temporal Tokens**: Credentials expire automatically after workflow
  completion
- **Audit Trail**: AWS CloudTrail logs all assumed role activities

## Security Considerations

### Access Control

- IAM role trust policy limits access to specific GitHub repository pattern:
  `repo:ORG/REPO:*`
- OIDC provider validates GitHub's SSL certificate thumbprint
- AWS STS tokens have maximum 1-hour lifetime

### Secrets Management

- GitHub PAT stored encrypted in AWS Secrets Manager
- No long-lived AWS credentials in GitHub repository secrets
- Role permissions follow principle of least privilege (currently
  Administrator for deployment needs)

### Monitoring

- AWS CloudTrail tracks all role assumption events
- GitHub Actions logs show authentication steps
- AWS IAM Access Analyzer identifies unused permissions

## Troubleshooting

### Common Issues

**OIDC Provider Creation Fails**

```bash
# Check existing providers
aws iam list-open-id-connect-providers

# Verify thumbprint
openssl s_client -connect token.actions.githubusercontent.com:443 \
  -servername token.actions.githubusercontent.com | \
  openssl x509 -fingerprint -sha1 -noout
```

**Role Assumption Denied**

- Verify repository name matches exactly in trust policy
- Check GitHub workflow has `id-token: write` permission
- Confirm OIDC provider ARN is correct in role trust relationship

**Lambda Function Errors**

```bash
# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# View recent errors
aws logs filter-log-events --log-group-name /aws/lambda/FUNCTION_NAME \
  --start-time 1640995200000
```

**CDK Deployment Issues**

```bash
# Clear CDK cache
rm -rf cdk.out/

# Retry with verbose output
cdk deploy --verbose

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name AuthBetweenAwsAndGithub
```

### Validation Commands

```bash
# Test role assumption from GitHub Actions
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::ACCOUNT:role/GitHubActionsRole \
  --role-session-name test-session \
  --web-identity-token $ACTIONS_ID_TOKEN_REQUEST_TOKEN

# Verify OIDC configuration
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com
```
