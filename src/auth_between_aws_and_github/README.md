# GitHub Actions Self-Hosted Runners Bootstrap

## Overview

A **completely self-contained, dependency-free** Python bootstrap script for automating AWS infrastructure setup for GitHub Actions self-hosted runners. This script implements AWS API calls using **pure Python standard library only** — no AWS CLI, boto3, or external dependencies required.

This is a production-ready solution that transitions your GitHub Actions workflows from human-managed credentials to **automatic OIDC-based authentication**, eliminating the need to maintain AWS access keys in GitHub Secrets.

## Purpose

This script automates the complete infrastructure bootstrap process for GitHub Actions self-hosted runners:

- **Creates an OIDC identity provider** linking GitHub Actions to your AWS account
- **Provisions an IAM role** with appropriate permissions for runner operations
- **Stores GitHub credentials** securely in AWS Secrets Manager
- **Enables model access** for AWS Bedrock (optional)
- **Automatically cleans up** human credentials from GitHub Secrets (transitioning to pure OIDC)
- **Supports complete resource destruction** when infrastructure is no longer needed

## Requirements

**Minimum Requirements:**
- Python 3.11+
- AWS account with appropriate IAM permissions
- GitHub organization with repository access
- GitHub Classic Personal Access Token (PAT) with `admin:org` and `repo` scopes

**Zero External Dependencies:**
- ✅ No AWS CLI required
- ✅ No boto3 or AWS SDKs
- ✅ No pip install or requirements.txt
- ✅ Uses only Python standard library (urllib, json, hashlib, hmac, ssl, xml.etree.ElementTree, etc.)

## Quick Start

### 1. Prepare Your Credentials

```bash
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"
export AWS_IAM_ROLE_NAME="GitHubActionsRole"
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export GITHUB_ORG="your-org"
export GITHUB_REPO="your-repo"
export GITHUB_TOKEN="ghp_your-classic-pat-token"
export GITHUB_PAT_SECRET_NAME="github-runner-pat"
```

### 2. Run Bootstrap (Cold Start)

```bash
python3 bootstrap.py create \
  --aws-account-id "$AWS_ACCOUNT_ID" \
  --aws-region "$AWS_REGION" \
  --aws-iam-role-name "$AWS_IAM_ROLE_NAME" \
  --aws-access-key-id "$AWS_ACCESS_KEY_ID" \
  --aws-secret-access-key "$AWS_SECRET_ACCESS_KEY" \
  --github-org "$GITHUB_ORG" \
  --github-repo "$GITHUB_REPO" \
  --github-token "$GITHUB_TOKEN" \
  --github-pat-secret-name "$GITHUB_PAT_SECRET_NAME"
```

### 3. Configure GitHub Actions Workflow

After bootstrap completes, your GitHub Actions workflows can authenticate using OIDC:

```yaml
name: Example Workflow
on: push
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials (pure OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Run infrastructure operations
        run: python3 bootstrap.py create --aws-account-id ...
```

## Architecture Overview

The bootstrap system operates in three distinct states:

### State 1: COLD (Initial Setup)
- No AWS infrastructure exists for GitHub Actions
- Credentials are human-managed in GitHub Secrets
- Bootstrap detects this state by checking for OIDC provider
- **Action:** Create OIDC provider, IAM role, and manage credentials manually

### State 2: WARM (Fully Bootstrapped)
- OIDC provider and IAM role already created
- GitHub Actions can authenticate using OIDC tokens
- Credentials stored in AWS Secrets Manager
- **Action:** Use OIDC for authentication; retrieve GitHub token from Secrets Manager

### State 3: DESTROY (Cleanup)
- Remove all bootstrap infrastructure
- Delete OIDC provider, IAM role, and stored credentials
- Restore manual credential management if needed

## Usage

### Create Bootstrap Resources

```bash
python3 bootstrap.py create \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsRole \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --github-org my-org \
  --github-repo my-repo \
  --github-token ghp_1234567890abcdefghijklmnopqrstuvwxyz \
  --github-pat-secret-name github-runner-pat \
  --enable-bedrock
```

**Options:**
- `--bedrock-model-id`: Specify Bedrock model (default: `us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- `--enable-bedrock`: Enable Anthropic model access (default: enabled)

### Destroy Bootstrap Resources

```bash
python3 bootstrap.py destroy \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsRole \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --github-org my-org \
  --github-repo my-repo \
  --github-pat-secret-name github-runner-pat \
  --force
```

**Options:**
- `--force`: Skip confirmation prompt

### Update README Documentation

```bash
python3 bootstrap.py readme \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsRole \
  --update
```

**Options:**
- `--check`: Check if README needs updating (outputs `true` or `false`)
- `--update`: Generate and write updated README
- `--output-file`: Write check result to file (CI/CD integration)

### Command-Line Options

```bash
python3 bootstrap.py --help                    # Show all commands
python3 bootstrap.py create --help             # Show create options
python3 bootstrap.py destroy --help            # Show destroy options
python3 bootstrap.py readme --help             # Show readme options
python3 bootstrap.py -v create ...             # Verbose output (DEBUG)
python3 bootstrap.py -q create ...             # Quiet output (ERROR only)
```

## Configuration Details

### AWS Permissions Required

The credentials used must have:

1. **IAM Permissions:**
   - `iam:CreateOpenIDConnectProvider`
   - `iam:DeleteOpenIDConnectProvider`
   - `iam:GetOpenIDConnectProvider`
   - `iam:CreateRole`
   - `iam:DeleteRole`
   - `iam:GetRole`
   - `iam:UpdateAssumeRolePolicy`
   - `iam:AttachRolePolicy`
   - `iam:DetachRolePolicy`
   - `iam:PutRolePolicy`
   - `iam:DeleteRolePolicy`
   - `iam:ListAttachedRolePolicies`

2. **Secrets Manager Permissions:**
   - `secretsmanager:CreateSecret`
   - `secretsmanager:UpdateSecret`
   - `secretsmanager:GetSecretValue`
   - `secretsmanager:DeleteSecret`
   - `secretsmanager:DescribeSecret`

3. **Bedrock Permissions (optional):**
   - `bedrock:ListFoundationModels`
   - `bedrock:PutUseCaseForModelAccess`
   - `bedrock:ListFoundationModelAgreementOffers`
   - `bedrock:CreateFoundationModelAgreement`
   - `bedrock:InvokeModel`

**Recommended Approach:** Attach `PowerUserAccess` managed policy plus `AdministratorAccess` for initial setup.

### GitHub PAT Requirements

The GitHub Personal Access Token must have:
- **Scopes:** `admin:org`, `repo`
- **Type:** Classic PAT (not fine-grained)
- **Expiration:** Configure based on your security policy

Generate at: https://github.com/settings/tokens/new?scopes=admin:org,repo

### Bedrock Model Configuration

The script supports multiple Bedrock models:

```bash
# Anthropic Claude (requires manual approval)
--bedrock-model-id us.anthropic.claude-haiku-4-5-20251001-v1:0

# Amazon Nova (available by default)
--bedrock-model-id us.amazon.nova-lite-v1:0
--bedrock-model-id us.amazon.nova-pro-v1:0
```

**Note:** Anthropic models require initial approval process (handled automatically).

## Authentication Methods

### Cold Start (Direct Credentials)

```bash
# Initial setup uses provided AWS credentials
python3 bootstrap.py create \
  --aws-access-key-id YOUR_KEY_ID \
  --aws-secret-access-key YOUR_SECRET_KEY \
  ...
```

### Warm State (OIDC in GitHub Actions)

Once bootstrapped, subsequent runs in GitHub Actions workflows use OIDC:

```yaml
permissions:
  id-token: write  # Required for OIDC token generation

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - run: python3 bootstrap.py create ...
```

The script automatically detects warm state and uses OIDC token instead of credentials.

## Implementation Details

### Pure Python Standard Library Architecture

This script is built entirely on Python's standard library, implementing AWS APIs without external dependencies:

**AWS Signature Version 4 Implementation:**
- Custom HMAC-SHA256 signing chain
- Canonical request building per AWS spec
- Support for Query, JSON, and REST API styles

**Supported AWS Services:**
- **IAM** (Query API) - Role and OIDC provider management
- **STS** (Query API) - OIDC token assumption
- **Secrets Manager** (JSON API) - Credential storage
- **Bedrock** (REST API) - Model access and invocation

**Network Features:**
- Automatic exponential backoff retry logic
- Timeout handling with configurable delays
- DNS failure recovery
- Connection pooling via urllib

### Why Standard Library Only?

1. **Zero Dependencies:** No `pip install`, no version conflicts, no supply chain risks
2. **Portability:** Runs anywhere Python 3.11+ is available
3. **Maintainability:** Complete source visibility, no external code to audit
4. **Efficiency:** Minimal startup time, smaller memory footprint
5. **Security:** No dependency updates to track, complete control over all code

### Key Classes

- **AWSClientBase:** Base class implementing AWS Signature Version 4 signing
- **STSClient:** Security Token Service operations (OIDC token assumption)
- **IAMClient:** Identity and Access Management operations
- **SecretsManagerClient:** AWS Secrets Manager operations
- **BedrockClient:** AWS Bedrock model invocation

## Security Considerations

### Credential Management

1. **During Cold Start:**
   - Credentials passed via command-line arguments
   - Stored temporarily in process memory
   - Deleted after initial resource creation
   - Not written to disk or logs

2. **During Warm State:**
   - OIDC tokens used for authentication
   - Tokens are short-lived (1 hour default)
   - GitHub Actions provides token automatically
   - No human credentials stored in Secrets

3. **GitHub PAT Storage:**
   - Stored encrypted in AWS Secrets Manager
   - Encrypted at rest by AWS
   - Encrypted in transit (TLS 1.2+)
   - Only accessed with appropriate IAM role permissions

### OIDC Benefits

- ✅ No long-lived credentials in GitHub Secrets
- ✅ Automatic token rotation every workflow run
- ✅ Fine-grained role assumption
- ✅ Complete audit trail in CloudTrail
- ✅ Compliance-friendly (SOC2, PCI-DSS)

### Audit Logging

All operations are logged to stderr:

```
2024-01-15 10:30:45 - Creating GitHub Actions OIDC provider
2024-01-15 10:30:46 - Created OIDC provider
2024-01-15 10:30:47 - Creating IAM role 'GitHubActionsRole'
...
```

Enable verbose output for debugging:
```bash
python3 bootstrap.py -v create ...
```

## Error Handling and Resilience

### Network Resilience

The script implements automatic retry logic for transient failures:

- **Exponential Backoff:** Retry delays increase: 1s, 2s, 4s, 8s
- **Jitter:** Random delay added to prevent thundering herd
- **Timeout Scaling:** Each retry increases timeout window
- **Maximum Attempts:** 4 attempts before failure

```
Attempt 1: timeout=30s, retry after ~1s
Attempt 2: timeout=60s, retry after ~2s
Attempt 3: timeout=120s, retry after ~4s
Attempt 4: timeout=240s (final attempt)
```

### Error Messages

Clear, actionable error messages guide troubleshooting:

```
FATAL: AWS credentials invalid or expired
ACTION: Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

FATAL: GitHub PAT missing required scopes: admin:org
ACTION: Create new PAT at https://github.com/settings/tokens/new?scopes=admin:org,repo
```

## Troubleshooting

### "AWS credentials invalid"

**Symptom:**
```
FATAL: STS access denied
Check that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
```

**Solution:**
1. Verify credentials are correct
2. Ensure credentials are for correct AWS account
3. Check credentials are not expired
4. Confirm user has `sts:GetCallerIdentity` permission

### "GitHub PAT invalid or expired"

**Symptom:**
```
FATAL: GitHub PAT is invalid or expired
```

**Solution:**
1. Generate new PAT at https://github.com/settings/tokens/new
2. Ensure scopes include `admin:org` and `repo`
3. Use Classic PAT (not fine-grained)
4. Update script arguments with new token

### "Missing required scopes"

**Symptom:**
```
FATAL: GitHub PAT missing required scopes: admin:org, repo
```

**Solution:**
```bash
# Create new PAT with correct scopes
# https://github.com/settings/tokens/new?scopes=admin:org,repo
```

### "Network error after 4 attempts"

**Symptom:**
```
Error: Network/timeout error after 4 attempts
```

**Solution:**
1. Check internet connectivity
2. Verify DNS resolution: `nslookup iam.amazonaws.com`
3. Check firewall/proxy settings
4. Verify AWS API endpoint accessibility
5. Run again with verbose mode: `python3 bootstrap.py -v create ...`

### "OIDC provider already exists"

**Symptom:**
```
State: WARM (infrastructure exists)
OIDC provider already exists, skipping creation
```

**Solution:**
This is normal for warm state. Script skips creation and proceeds. If you need to recreate:
```bash
python3 bootstrap.py destroy --force ...
python3 bootstrap.py create ...
```

### "IAM role in warm state, but trust policy differs"

**Symptom:**
```
IAM role already exists, checking trust policy
Trust policy differs, updating
```

**Solution:**
This is expected when bootstrap detects changed configuration (different org/repo). Trust policy is automatically updated.

### "OIDC role missing PowerUserAccess policy"

**Symptom:**
```
FATAL: OIDC role 'GitHubActionsRole' missing PowerUserAccess managed policy
```

**Solution:**
Re-run create command. Script will attach required policies.

### Verbose Debugging

Enable debug output to see detailed operation logs:

```bash
python3 bootstrap.py -v create \
  --aws-account-id 123456789012 \
  ...
```

This enables:
- Full HTTP request/response logging
- Detailed AWS API call tracing
- XML/JSON response parsing logs
- OIDC token validation details

## Environment Variables

The script respects AWS environment variables:

```bash
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

python3 bootstrap.py create \
  --aws-account-id 123456789012 \
  ...
```

GitHub Actions environment variables for OIDC:
- `GITHUB_ACTIONS=true` - Script detects workflow context
- `ACTIONS_ID_TOKEN_REQUEST_URL` - OIDC token endpoint
- `ACTIONS_ID_TOKEN_REQUEST_TOKEN` - Token request credential

## Monitoring and Maintenance

### Verify Bootstrap Status

Check if infrastructure is bootstrapped:

```bash
python3 bootstrap.py create --help  # Shows current state in output
```

Or query AWS directly:

```bash
aws iam get-openid-connect-provider \
  --open-id-connect-provider-arn "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"

aws iam get-role --role-name GitHubActionsRole
```

### Update Credentials

To rotate GitHub PAT:

1. Generate new GitHub PAT
2. Manually update in AWS Secrets Manager:
   ```bash
   aws secretsmanager update-secret \
     --secret-id github-runner-pat \
     --secret-string '{"auth_method":"classic-pat","github_token":"ghp_new_token","github_org":"org","github_repo":"repo"}'
   ```
3. Or re-run bootstrap with new token

### Disaster Recovery

Complete cleanup and restart:

```bash
# 1. Destroy all infrastructure
python3 bootstrap.py destroy --force \
  --aws-account-id 123456789012 \
  ...

# 2. Verify cleanup
aws iam list-open-id-connect-providers
aws iam get-role --role-name GitHubActionsRole  # Should fail

# 3. Re-bootstrap
python3 bootstrap.py create \
  --aws-account-id 123456789012 \
  ...
```

## Examples

### Example 1: GitHub Organization Bootstrap

```bash
# Setup for entire organization
python3 bootstrap.py create \
  --aws-account-id 123456789012 \
  --aws-region us-east-1 \
  --aws-iam-role-name GitHubActionsOrgRole \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --github-org my-org \
  --github-repo my-central-repo \
  --github-token ghp_1234567890abcdefghijklmnopqrstuvwxyz \
  --github-pat-secret-name org-github-pat \
  --enable-bedrock
```

### Example 2: Headless CI/CD Integration

```bash
#!/bin/bash
# ci/bootstrap.sh

set -euo pipefail

python3 bootstrap.py create \
  --aws-account-id "$AWS_ACCOUNT_ID" \
  --aws-region "$AWS_REGION" \
  --aws-iam-role-name "$AWS_IAM_ROLE_NAME" \
  --aws-access-key-id "$AWS_ACCESS_KEY_ID" \
  --aws-secret-access-key "$AWS_SECRET_ACCESS_KEY" \
  --github-org "$GITHUB_ORG" \
  --github-repo "$GITHUB_REPO" \
  --github-token "$GITHUB_TOKEN" \
  --github-pat-secret-name "$GITHUB_PAT_SECRET_NAME" \
  --bedrock-model-id "us.amazon.nova-pro-v1:0"

echo "Bootstrap completed successfully"
```

### Example 3: GitHub Actions Workflow

```yaml
name: Bootstrap Runner Infrastructure
on:
  workflow_dispatch:
  
permissions:
  id-token: write
  contents: read

env:
  AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
  AWS_REGION: us-east-1
  AWS_IAM_ROLE_NAME: GitHubActionsRole
  GITHUB_ORG: my-org
  GITHUB_REPO: my-repo
  GITHUB_PAT_SECRET_NAME: github-runner-pat

jobs:
  bootstrap:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ env.AWS_ACCOUNT_ID }}:role/${{ env.AWS_IAM_ROLE_NAME }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Run bootstrap
        run: |
          python3 bootstrap.py create \
            --aws-account-id "${{ env.AWS_ACCOUNT_ID }}" \
            --aws-region "${{ env.AWS_REGION }}" \
            --aws-iam-role-name "${{ env.AWS_IAM_ROLE_NAME }}" \
            --github-org "${{ env.GITHUB_ORG }}" \
            --github-repo "${{ env.GITHUB_REPO }}" \
            --github-token "${{ secrets.GITHUB_TOKEN }}" \
            --github-pat-secret-name "${{ env.GITHUB_PAT_SECRET_NAME }}"
```

## Contributing

To modify or extend this script:

1. **Preserve stdlib-only architecture** - No external dependencies
2. **Maintain AWS Sig V4 compatibility** - Keep signing implementation current
3. **Add tests** for new AWS service integrations
4. **Update README** using `python3 bootstrap.py readme --update`
5. **Document changes** clearly in commit messages

## License

This project is provided as-is. See LICENSE file for details.

## Support

For issues or questions:

1. Check the **Troubleshooting** section above
2. Enable verbose logging: `python3 bootstrap.py -v create ...`
3. Review AWS CloudTrail logs for API errors
4. Check GitHub Actions logs for authentication issues

---

**Built with:** Pure Python 3.11+ standard library  
**AWS Services:** IAM, STS, Secrets Manager, Bedrock  
**No External Dependencies** ✨