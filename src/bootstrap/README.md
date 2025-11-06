# GitHub Actions Self-Hosted Runners Bootstrap

This script automates the setup and teardown of AWS infrastructure for GitHub Actions self-hosted runners.

## Purpose

This script facilitates the bootstrapping of AWS resources required for GitHub Actions self-hosted runners, including the creation of IAM roles, OIDC providers, and necessary secrets.

## Requirements

- Python 3.7 or higher
- AWS CLI configured with appropriate permissions
- GitHub Personal Access Token with `admin:org` and `repo` scopes

## Usage Instructions

### Creating Resources

To create the necessary AWS resources, run the script with the `create` command and provide the required arguments:

```bash
python bootstrap.py create \
  --aws-access-key-id YOUR_AWS_ACCESS_KEY_ID \
  --aws-account-id YOUR_AWS_ACCOUNT_ID \
  --aws-iam-role-name YOUR_IAM_ROLE_NAME \
  --aws-region YOUR_AWS_REGION \
  --aws-secret-access-key YOUR_AWS_SECRET_ACCESS_KEY \
  --github-org YOUR_GITHUB_ORG \
  --github-repo YOUR_GITHUB_REPO \
  --github-token YOUR_GITHUB_TOKEN \
  --github-pat-secret-name YOUR_GITHUB_PAT_SECRET_NAME \
  [--bedrock-model-id YOUR_BEDROCK_MODEL_ID] \
  [--enable-bedrock]
```

### Destroying Resources

To destroy the created AWS resources, run the script with the `destroy` command and provide the required arguments:

```bash
python bootstrap.py destroy \
  --aws-access-key-id YOUR_AWS_ACCESS_KEY_ID \
  --aws-account-id YOUR_AWS_ACCOUNT_ID \
  --aws-iam-role-name YOUR_IAM_ROLE_NAME \
  --aws-region YOUR_AWS_REGION \
  --aws-secret-access-key YOUR_AWS_SECRET_ACCESS_KEY \
  --github-org YOUR_GITHUB_ORG \
  --github-repo YOUR_GITHUB_REPO \
  --github-pat-secret-name YOUR_GITHUB_PAT_SECRET_NAME \
  [--force]
```

### Checking or Updating the README

To check if the README needs an update or to generate and update it, run the script with the `readme` command:

```bash
python bootstrap.py readme \
  --aws-account-id YOUR_AWS_ACCOUNT_ID \
  --aws-iam-role-name YOUR_IAM_ROLE_NAME \
  --aws-region YOUR_AWS_REGION \
  [--check] \
  [--update] \
  [--output-file OUTPUT_FILE]
```

## Architecture Overview

The script operates in three states:

- **COLD**: No infrastructure exists.
- **WARM**: Infrastructure exists.
- **DESTROY**: Resources are being deleted.

## Configuration Details

- **AWS Credentials**: Can be provided directly or assumed via OIDC.
- **GitHub Secrets**: GitHub Personal Access Token stored in AWS Secrets Manager.

## Authentication Methods

- **OIDC**: Used when infrastructure exists.
- **Direct Credentials**: Used for cold starts.

## Implementation Details

- **Pure Python stdlib**: Utilizes Python's standard library for AWS API requests.
- **AWS API Clients**: Implements custom clients for IAM, STS, Secrets Manager, and Bedrock services.

## Security Considerations

- Ensure IAM roles have the minimum required permissions.
- Store sensitive information like GitHub PAT in AWS Secrets Manager.
- Use OIDC for secure authentication when infrastructure exists.

## Troubleshooting Tips

- Check AWS CloudWatch logs for errors.
- Ensure all required permissions are granted in IAM roles.
- Validate GitHub PAT scopes to include `admin:org` and `repo`.

For more detailed troubleshooting, refer to the [official AWS documentation](https://docs.aws.amazon.com/) and [GitHub documentation](https://docs.github.com/).

---

This README provides a comprehensive overview of the bootstrap script for setting up AWS infrastructure for GitHub Actions self-hosted runners. For further details, refer to the script and respective AWS/GitHub documentation.