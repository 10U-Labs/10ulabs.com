# AWS-GitHub OIDC Authentication Infrastructure

This AWS CDK infrastructure sets up OpenID Connect (OIDC) authentication
between AWS and GitHub Actions, enabling secure, keyless authentication for
CI/CD workflows without storing long-lived AWS credentials in GitHub Secrets.

## Purpose and Key Features

- **Keyless Authentication**: Eliminates the need for AWS access keys in
  GitHub Secrets
- **Enhanced Security**: Uses short-lived tokens with specific repository
  permissions
- **Automated Setup**: Deploys complete OIDC infrastructure via AWS CDK
- **GitHub Integration**: Seamlessly works with GitHub Actions workflows
- **Custom Lambda Functions**: Handles OIDC provider and IAM role creation
  with proper error handling

## Resources Created

This infrastructure creates the following AWS resources:

- **GitHub OIDC Identity Provider**: Enables GitHub Actions to authenticate
  with AWS using JWT tokens
- **IAM Role for GitHub Actions**: Role that GitHub Actions can assume with
  AdministratorAccess permissions
- **Lambda Functions**: Custom resources for managing OIDC provider and IAM
  role lifecycle
- **IAM Roles for Lambda**: Service roles with permissions to manage OIDC
  providers and IAM roles
- **Secrets Manager Integration**: References existing GitHub PAT secret for
  workflow automation

## Prerequisites and Requirements

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages from `requirements.txt`:

- `aws-cdk-lib>=2.100.0` - AWS CDK framework
- `constructs>=10.0.0` - CDK constructs library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[iam,sts,secretsmanager,bedrock-runtime]>=1.34.0` - Type stubs
- `typeguard==2.13.3` - Runtime type checking

### System Dependencies

- **Node.js 18+**: Required for AWS CDK CLI
- **Python 3.11+**: Runtime for Lambda functions and CDK application
- **Git**: For repository operations

### AWS Prerequisites

- AWS account with appropriate permissions
- AWS credentials configured (for initial deployment)
- Secrets Manager secret containing GitHub Personal Access Token

### GitHub Prerequisites

- GitHub repository with Actions enabled
- GitHub Personal Access Token with `admin:org` and `repo` scopes
- Repository secrets configured (for cold start deployment)

## Configuration

### config.json Structure

The `config.json` file contains all deployment configuration:

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

The `cdk.json` file configures CDK behavior with modern feature flags and
file watching capabilities for development workflows.

## Usage Instructions

### Initial Setup (Cold Start)

1. **Create AWS IAM User**:

   ```bash
   # Navigate to AWS IAM Console
   # Create user with AdministratorAccess policy
   # Generate access key pair
   ```

2. **Create GitHub Personal Access Token**:
   - Go to <https://github.com/settings/tokens>
   - Create Classic PAT with `admin:org` and `repo` scopes

3. **Configure GitHub Secrets**:

   ```bash
   # Add these secrets to your GitHub repository:
   # AWS_ACCESS_KEY_ID
   # AWS_SECRET_ACCESS_KEY  
   # GH_RUNNER_PAT
   ```

4. **Deploy Infrastructure**:

   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Deploy stack
   cdk deploy --require-approval never
   ```

### Local Development Deployment

```bash
# Navigate to project directory
cd auth_between_aws_and_github

# Install dependencies
pip install -r requirements.txt

# Deploy with GitHub token context
cdk deploy --require-approval never -c github_token=YOUR_GITHUB_PAT
```

### Using in GitHub Actions

After deployment, update your GitHub Actions workflows:

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
          role-to-assume: arn:aws:iam::781581267945:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Deploy infrastructure
        run: |
          cdk deploy --require-approval never
```

## Architecture Overview

### Authentication Flow

1. **GitHub Actions Trigger**: Workflow runs in specified repository
2. **OIDC Token Request**: GitHub generates JWT token with repository claims
3. **AWS STS AssumeRole**: Token exchanged for temporary AWS credentials
4. **Role Validation**: Trust policy validates repository and organization
5. **Credential Usage**: Temporary credentials used for AWS operations

### Component Interactions

```text
GitHub Actions → OIDC Provider → IAM Role → AWS Resources
     ↓              ↓             ↓           ↓
   JWT Token    Token Validation  Assume    Temporary
                                  Role      Credentials
```

### Trust Policy Structure

The IAM role trust policy restricts access to:

- Specific GitHub organization and repository
- GitHub Actions audience (`sts.amazonaws.com`)
- Repository-scoped subject claims (`repo:org/repo:*`)

## Security Considerations

### Access Controls

The infrastructure implements several security layers:

- **Repository Scoping**: Trust policy limits access to specific repository
- **Audience Validation**: Ensures tokens are intended for AWS STS
- **Subject Matching**: Validates repository context in JWT claims
- **Time-Limited Tokens**: Uses short-lived credentials (1 hour default)

### Best Practices

- **Least Privilege**: Consider reducing from AdministratorAccess for
  production workloads
- **Environment Separation**: Use different roles for dev/staging/production
- **Audit Logging**: Monitor CloudTrail for role assumption events
- **Secret Rotation**: Regularly rotate GitHub Personal Access Tokens

### Sensitive Data Handling

- GitHub PAT stored in AWS Secrets Manager
- No long-lived credentials in GitHub repository
- Lambda functions use service-linked roles with minimal permissions

## Troubleshooting

### Common Issues

**OIDC Provider Already Exists**:

```bash
# Check existing providers
aws iam list-open-id-connect-providers
```

**Role Assumption Failures**:

```bash
# Verify trust policy
aws iam get-role --role-name GitHubActionsRole
```

**Lambda Function Errors**:

```bash
# Check CloudWatch Logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
```

### Debugging Steps

1. **Verify Configuration**: Check `config.json` values match your setup
2. **Check Permissions**: Ensure deployment credentials have IAM permissions
3. **Review CloudFormation**: Check stack events for deployment issues
4. **Test Locally**: Use `cdk diff` to preview changes before deployment

### Stack Management

```bash
# View stack differences
cdk diff

# Destroy infrastructure (manual only)
cdk destroy

# List all stacks
cdk list
```
