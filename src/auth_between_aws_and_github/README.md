# AWS-GitHub Authentication Infrastructure

**Self-Contained, Dependency-Free AWS-GitHub OIDC Authentication Manager**

A pure Python standard library implementation for managing AWS-GitHub authentication infrastructure. This script creates and manages the complete OIDC trust relationship between AWS and GitHub Actions, enabling secure, keyless authentication without any external dependencies.

## 🚀 Key Features

- **Zero Dependencies**: Uses only Python standard library - no pip, boto3, or AWS CLI required
- **Self-Contained**: Single file solution with custom AWS API client implementation
- **Pure Stdlib**: All AWS API calls implemented using urllib and standard cryptographic libraries
- **OIDC Authentication**: Enables secure, temporary credential access for GitHub Actions
- **State Management**: Intelligent three-state system (COLD/WARM/DESTROY) with automatic detection
- **Bedrock Integration**: Built-in documentation generation using AWS Bedrock AI models

## Requirements

- **Python 3.11+** (only requirement)
- **No AWS CLI required** - uses pure Python stdlib
- **No external dependencies** - no pip install needed
- **No boto3 or AWS SDKs** - custom implementation included

## Architecture Overview

The script operates in three distinct states:

### COLD State
- No infrastructure exists
- Uses direct AWS credentials (access key/secret key)
- Creates OIDC provider, IAM role, and stores secrets
- Transitions to WARM state upon completion

### WARM State
- Infrastructure exists and is operational
- Uses OIDC authentication in GitHub Actions workflows
- Can retrieve stored credentials from AWS Secrets Manager
- Automatically deletes human credentials to enforce pure OIDC

### DESTROY State
- Safely removes all created infrastructure
- Supports both OIDC and direct credential authentication
- Confirmation prompts prevent accidental deletion

## Usage

### Creating Infrastructure

```bash
# Initial setup (COLD -> WARM transition)
python auth_between_aws_and_github.py create \
  --aws-access-key-id "AKIA..." \
  --aws-secret-access-key "..." \
  --aws-account-id "123456789012" \
  --aws-region "us-east-1" \
  --aws-iam-role-name "GitHubActionsRole" \
  --github-org "your-org" \
  --github-repo "your-repo" \
  --github-token "ghp_..." \
  --github-pat-secret-name "github-runner-credentials" \
  --bedrock-model-id "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### Destroying Infrastructure

```bash
# Remove all infrastructure
python auth_between_aws_and_github.py destroy \
  --aws-access-key-id "AKIA..." \
  --aws-secret-access-key "..." \
  --aws-account-id "123456789012" \
  --aws-region "us-east-1" \
  --aws-iam-role-name "GitHubActionsRole" \
  --github-org "your-org" \
  --github-repo "your-repo" \
  --github-pat-secret-name "github-runner-credentials" \
  --force
```

### README Management

```bash
# Check if README needs updating
python auth_between_aws_and_github.py readme \
  --aws-account-id "123456789012" \
  --aws-region "us-east-1" \
  --aws-iam-role-name "GitHubActionsRole" \
  --check

# Update README using Bedrock AI
python auth_between_aws_and_github.py readme \
  --aws-account-id "123456789012" \
  --aws-region "us-east-1" \
  --aws-iam-role-name "GitHubActionsRole" \
  --update
```

## GitHub Actions Integration

### Workflow Configuration

```yaml
name: AWS Infrastructure Management
on: [push, pull_request]

permissions:
  id-token: write  # Required for OIDC
  contents: read

jobs:
  manage-infrastructure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Infrastructure
        run: |
          python auth_between_aws_and_github.py create \
            --aws-access-key-id "${{ secrets.AWS_ACCESS_KEY_ID }}" \
            --aws-secret-access-key "${{ secrets.AWS_SECRET_ACCESS_KEY }}" \
            --aws-account-id "123456789012" \
            --aws-region "us-east-1" \
            --aws-iam-role-name "GitHubActionsRole" \
            --github-org "${{ github.repository_owner }}" \
            --github-repo "${{ github.event.repository.name }}" \
            --github-token "${{ secrets.GH_RUNNER_PAT }}" \
            --github-pat-secret-name "github-runner-credentials" \
            --bedrock-model-id "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### Required GitHub Secrets (Initial Setup Only)

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
GH_RUNNER_PAT=ghp_...
```

**Note**: These secrets are automatically deleted after infrastructure creation, transitioning to pure OIDC authentication.

## Authentication Methods

### Direct Credentials (COLD State)
- Uses AWS access key and secret key
- Required for initial infrastructure creation
- Automatically phased out after WARM transition

### OIDC Authentication (WARM State)
- Uses temporary credentials via GitHub's OIDC provider
- No long-lived credentials stored in GitHub
- Automatic credential assumption in workflows

## Implementation Details

### Custom AWS Client Architecture

The script implements a complete AWS API client using only Python standard library:

- **AWSClientBase**: Core AWS API v4 signature implementation
- **STSClient**: Security Token Service operations
- **IAMClient**: Identity and Access Management operations  
- **SecretsManagerClient**: Secrets Manager operations
- **BedrockClient**: AI model operations for documentation

### Key Components

```python
# AWS API Signature v4 Implementation
def _sign_request(self, method: str, service: str, *, request_data: Dict[str, Any]) -> Dict[str, str]:
    # Pure stdlib implementation of AWS signature process
    
# HTTP Client with Retry Logic
def _retry_with_backoff(self, req: urllib.request.Request) -> str:
    # Exponential backoff with jitter for reliability
    
# OIDC Token Acquisition
def get_oidc_token() -> Optional[str]:
    # GitHub Actions OIDC token retrieval
```

## Configuration

### AWS Permissions Required

The script requires AWS credentials with the following permissions:

- **IAM**: Full access for OIDC provider and role management
- **STS**: GetCallerIdentity and AssumeRoleWithWebIdentity
- **Secrets Manager**: Full access for credential storage
- **Bedrock**: Model access for documentation generation

### GitHub PAT Requirements

GitHub Personal Access Token must have these scopes:

- **admin:org**: Organization runner management
- **repo**: Repository secrets management

## Security Considerations

### Credential Lifecycle Management

1. **Initial Setup**: Uses human-provided AWS credentials and GitHub PAT
2. **Transition**: Stores GitHub PAT in AWS Secrets Manager
3. **Automation**: Deletes human credentials from GitHub Secrets
4. **Operation**: Uses only OIDC temporary credentials

### Trust Policy Configuration

The IAM role trust policy restricts access to:
- Specific GitHub organization and repository
- GitHub Actions OIDC provider only
- Audience validation for AWS STS

### Best Practices

- Rotate GitHub PATs regularly
- Monitor AWS CloudTrail for authentication events
- Use least-privilege IAM policies when possible
- Enable AWS CloudWatch for monitoring

## Troubleshooting

### Common Issues

**"Failed to assume role with OIDC"**
```
Cause: OIDC provider or IAM role not properly configured
Solution: Run create command to ensure infrastructure exists
```

**"GitHub PAT missing required scopes"**
```
Cause: Insufficient GitHub token permissions
Solution: Create new PAT with admin:org and repo scopes
```

**"AWS API error 403"**
```
Cause: Insufficient AWS permissions
Solution: Ensure AWS credentials have AdministratorAccess or equivalent
```

**"Network timeout errors"**
```
Cause: Connectivity issues with AWS or GitHub APIs
Solution: Script includes automatic retry with exponential backoff
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python auth_between_aws_and_github.py create --verbose [other-args]
```

### State Detection

Check current infrastructure state:

```bash
# The script automatically detects and reports current state
python auth_between_aws_and_github.py create [args]
# Output includes: State: COLD/WARM, Mode: Workflow/Local, Auth: OIDC/Direct
```

## Advanced Usage

### Custom Bedrock Models

Support for different AI models for documentation:

```bash
# Use different Bedrock model
--bedrock-model-id "anthropic.claude-3-sonnet-20240229-v1:0"
--bedrock-model-id "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### Quiet/Verbose Modes

```bash
# Minimal output
python auth_between_aws_and_github.py create --quiet [args]

# Debug information
python auth_between_aws_and_github.py create --verbose [args]
```

### Force Operations

```bash
# Skip confirmation prompts
python auth_between_aws_and_github.py destroy --force [args]
```

## License

This project is provided as-is for AWS-GitHub integration automation. Review and modify according to your organization's security requirements.

---

**🎯 Result**: A completely self-contained, dependency-free solution for AWS-GitHub OIDC authentication that transitions your workflows from human credentials to fully automated, secure token-based authentication.