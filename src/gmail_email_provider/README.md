# Gmail Email Provider CDK Stack

This AWS CDK project configures DNS records for Gmail email services on a custom domain using Amazon Route 53. It sets up the necessary MX records and Google site verification TXT records to enable Gmail as the email provider for your domain.

## Overview

The stack creates:
- **MX Record**: Points email traffic to Gmail's SMTP servers (`smtp.google.com`)
- **TXT Record**: Google site verification record for domain ownership validation

## Prerequisites

- **Python 3.7+**
- **AWS CDK CLI** installed and configured
- **AWS CLI** configured with appropriate credentials
- **Existing Route 53 Hosted Zone** for your domain with exported values:
  - `{domain-name}-HostedZoneId`
  - `{domain-name}-HostedZoneName`
- **Google Workspace** or Gmail account configured for your domain

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` to match your environment:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_reasoning": 4000,
      "max_tokens_generation": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  },
  "domain_name": "10ulabs.com",
  "google_site_verification": "vkFVA-Ru1PwnePtOWeOt0k5bmzOpHtjfDZU-PfUKjRM",
  "ttl": 300
}
```

### Configuration Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `aws.account_id` | Your AWS account ID | Yes |
| `aws.region` | AWS region for deployment | Yes |
| `domain_name` | Your domain name | Yes |
| `google_site_verification` | Google site verification token | Yes |
| `ttl` | DNS record TTL in seconds | No (default: 300) |

## Deployment

1. **Bootstrap CDK (first time only):**
   ```bash
   cdk bootstrap
   ```

2. **Deploy the stack:**
   ```bash
   cdk deploy
   ```

3. **View changes before deployment:**
   ```bash
   cdk diff
   ```

## Stack Outputs

After successful deployment, the stack provides:

- **GoogleVerificationRecord**: Domain name of the Google verification TXT record
- **GoogleVerificationValue**: The verification token value
- **GmailMxRecordOutput**: Domain name of the Gmail MX record

## DNS Records Created

### MX Record
- **Name**: `@` (root domain)
- **Type**: MX
- **Priority**: 1
- **Value**: `smtp.google.com.`

### TXT Record
- **Name**: `@` (root domain)
- **Type**: TXT
- **Value**: `google-site-verification={your-verification-token}`

## Development

### File Structure

```
├── app.py              # CDK application entry point
├── stack.py            # Gmail provider stack definition
├── config.json         # Configuration file
├── cdk.json           # CDK configuration
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

### Watch Mode

For development, you can use CDK watch mode to automatically redeploy on changes:

```bash
cdk watch
```

### Useful CDK Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk deploy` - Deploy the stack
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy` - Delete the stack

## Dependencies

- **aws-cdk-lib**: AWS CDK core library
- **constructs**: CDK constructs framework
- **boto3**: AWS SDK for Python
- **boto3-stubs**: Type hints for boto3

## Troubleshooting

### Common Issues

1. **Missing Hosted Zone Exports**: Ensure your domain's hosted zone exports the required values with the correct naming convention.

2. **Invalid Google Verification Token**: Obtain the correct verification token from Google Search Console.

3. **Permission Errors**: Ensure your AWS credentials have permissions for Route 53 operations.

### Verification

After deployment, verify the DNS records:

```bash
# Check MX record
dig MX yourdomain.com

# Check TXT record
dig TXT yourdomain.com
```

## Tags

The stack automatically applies these tags to all resources:
- `ManagedBy`: CDK
- `Project`: 10UF
- `Repository`: 10U-Foundation/10ulabs.com
