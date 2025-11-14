# AWS-GitHub OIDC Authentication Infrastructure

This CDK infrastructure automates the setup of OpenID Connect (OIDC)
authentication between AWS and GitHub Actions, enabling secure, keyless
authentication for CI/CD workflows without storing long-lived AWS credentials
in GitHub secrets.

## Overview

This project creates the necessary AWS resources to establish trust between
GitHub Actions and AWS using OIDC federation. It eliminates the need to
store AWS access keys in GitHub secrets by leveraging temporary credentials
through web identity federation.

## Key Features

- **Keyless Authentication**: No AWS access keys stored in GitHub
- **Automated Setup**: Complete OIDC provider and IAM role configuration
- **Secure by Design**: Uses temporary credentials with assumed roles
- **Repository-Specific**: IAM roles scoped to specific GitHub repositories
- **Custom Resource Management**: Lambda-based custom resources for
  fine-grained control

## Resources Created

### AWS Resources

| Resource Type | Name/Purpose | Description |
|---------------|--------------|-------------|
| **OIDC Provider** | GitHub Actions OIDC | Establishes trust with GitHub's token service |
| **IAM Role** | GitHub Actions Execution Role | Role assumed by GitHub Actions workflows |
| **Lambda Function** | OIDC Provider Manager | Creates/manages the OIDC provider |
| **Lambda Function** | IAM Role Manager | Creates/manages the GitHub Actions IAM role |
| **IAM Role** | OIDC Lambda Execution Role | Execution role for OIDC provider Lambda |
| **IAM Role** | IAM Lambda Execution Role | Execution role for IAM role manager Lambda |
| **Custom Resource** | GitHubOIDCProvider | Custom resource for OIDC provider lifecycle |
| **Custom Resource** | GitHubActionsRole | Custom resource for IAM role lifecycle |
| **Secrets Manager Secret** | GitHub PAT Secret | Reference to existing GitHub PAT secret |

### Key Configurations

- **OIDC Provider URL**: `https://token.actions.githubusercontent.com`
- **Audience**: `sts.amazonaws.com`
- **Thumbprint**: `6938fd4d98bab03faadb97b34396831e3780aea1`
- **Permissions**: AdministratorAccess (configurable)

## Prerequisites

### Required Software

- Python 3.8 or later
- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Git

### Required AWS Permissions

The deploying user/role needs permissions for:

- IAM role and policy management
- Lambda function management
- CloudFormation stack operations
- Secrets Manager access

### Required Dependencies

```python
aws-cdk-lib>=2.0.0
constructs>=10.0.0
```

## Configuration

Create a `config.json` file in the project root:

```json
{
  "aws": {
    "account_id": "123456789012",
    "region": "us-east-1",
    "iam_role_name": "GitHubActionsRole",
    "secrets_manager": {
      "github_pat_secret_name": "github-pat-secret"
    }
  },
  "github": {
    "org": "your-github-org",
    "repo": "your-repository-name"
  }
}
```

### Configuration Parameters

- **aws.account_id**: Your AWS account ID
- **aws.region**: AWS region for deployment
- **aws.iam_role_name**: Name for the GitHub Actions IAM role
- **aws.secrets_manager.github_pat_secret_name**: Name of existing GitHub PAT
  secret in Secrets Manager
- **github.org**: GitHub organization name
- **github.repo**: GitHub repository name

## Installation and Deployment

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd aws-github-oidc-auth
```

### Step 2: Install Dependencies

```bash
pip install aws-cdk-lib constructs
```

### Step 3: Configure AWS CLI

```bash
aws configure
# or use existing AWS credentials/profile
export AWS_PROFILE=your-profile
```

### Step 4: Create Configuration

```bash
cp config.json.example config.json
# Edit config.json with your values
```

### Step 5: Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy
```

### Step 6: Verify Deployment

```bash
# List the created resources
aws iam list-open-id-connect-providers
aws iam get-role --role-name GitHubActionsRole
```

## Usage in GitHub Actions

After deployment, configure your GitHub Actions workflow:

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT-ID:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Test AWS Access
        run: aws sts get-caller-identity
```

## Architecture Overview

### Authentication Flow

1. **GitHub Actions Workflow Triggers**: Workflow starts with `id-token: write`
   permission
2. **Token Request**: GitHub Actions requests OIDC token from GitHub's token
   service
3. **AWS STS Call**: Workflow calls `sts:AssumeRoleWithWebIdentity` with the
   OIDC token
4. **Token Validation**: AWS validates token against registered OIDC provider
5. **Role Assumption**: If valid, AWS returns temporary credentials for the
   specified IAM role
6. **AWS API Access**: Workflow uses temporary credentials for AWS operations

### Component Interaction

```text
GitHub Actions → OIDC Token → AWS STS → Temporary Credentials → AWS Services
```

### Trust Relationship

The IAM role trusts GitHub's OIDC provider with conditions:

- **Audience**: Must be `sts.amazonaws.com`
- **Subject**: Must match `repo:ORG/REPO:*` pattern
- **Provider**: Must be GitHub's token service

## Security Considerations

### Security Best Practices

- **Least Privilege**: Consider replacing `AdministratorAccess` with
  specific permissions
- **Repository Scoping**: Roles are scoped to specific GitHub repositories
- **Temporary Credentials**: No long-lived credentials stored in GitHub
- **Audience Validation**: OIDC tokens validated for correct audience

### Recommended Security Enhancements

1. **Custom IAM Policies**: Replace `AdministratorAccess` with specific
   permissions:

   ```python
   # In the Lambda function, replace AdministratorAccess with:
   custom_policy = {
       "Version": "2012-10-17",
       "Statement": [{
           "Effect": "Allow",
           "Action": [
               "s3:GetObject",
               "s3:PutObject",
               "cloudformation:*"
           ],
           "Resource": "*"
       }]
   }
   ```

2. **Branch Conditions**: Restrict to specific branches:

   ```json
   "StringLike": {
     "token.actions.githubusercontent.com:sub": "repo:org/repo:ref:refs/heads/main"
   }
   ```

3. **Time-based Conditions**: Add time restrictions if needed
4. **IP Restrictions**: Consider IP-based conditions for additional security

### Secrets Management

- GitHub PAT secret must exist in AWS Secrets Manager before deployment
- Secret ARN is exposed as stack output for reference
- Rotate GitHub PATs regularly

## Troubleshooting

### Common Issues

#### 1. OIDC Provider Already Exists

**Error**: `EntityAlreadyExistsException`

**Solution**: The Lambda function handles existing providers gracefully.
Redeploy if needed.

#### 2. Permission Denied During Deployment

**Error**: `AccessDeniedException`

**Solution**: Ensure deploying user has IAM permissions:

```bash
aws iam attach-user-policy --user-name YOUR_USER \
  --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
```

#### 3. GitHub Actions Role Assumption Fails

**Error**: `Not authorized to perform sts:AssumeRoleWithWebIdentity`

**Solutions**:

- Verify `id-token: write` permission in workflow
- Check repository name matches configuration
- Ensure OIDC provider exists and is configured correctly

#### 4. Configuration File Not Found

**Error**: `FileNotFoundError: config.json`

**Solution**: Create `config.json` in the same directory as `app.py`

### Debugging Commands

```bash
# Check OIDC provider
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com

# Check IAM role
aws iam get-role --role-name GitHubActionsRole

# Test role assumption (from GitHub Actions)
aws sts get-caller-identity

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name AuthBetweenAwsAndGithub
```

### Log Analysis

- **Lambda Logs**: Check CloudWatch logs for custom resource Lambdas
- **CloudFormation Events**: Monitor stack deployment progress
- **GitHub Actions Logs**: Review workflow execution logs for authentication
  issues

## Cleanup

To remove all created resources:

```bash
cdk destroy
```

**Note**: Custom resources may require manual cleanup if Lambda functions
fail during deletion.
