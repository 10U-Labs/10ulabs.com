# Gmail Email Provider Infrastructure

This AWS CDK infrastructure sets up DNS configuration for Gmail email
services on the 10ulabs.com domain. It creates the necessary Route 53
DNS records to enable Gmail as the email provider, including MX records
for mail routing and Google site verification records.

## Purpose and Key Features

- **Gmail Integration**: Configures DNS records to route email through
  Gmail's SMTP servers
- **Domain Verification**: Sets up Google site verification for domain
  ownership confirmation
- **DNS Management**: Manages Route 53 records for email services
- **Infrastructure as Code**: Uses AWS CDK for reproducible deployments

## Resources Created

This infrastructure creates the following AWS resources:

### Route 53 Records

- **MX Record**: Routes email traffic to `smtp.google.com` with priority 1
- **TXT Record**: Google site verification record for domain ownership

### CloudFormation Outputs

- **GoogleVerificationRecord**: Domain name of the verification record
- **GoogleVerificationValue**: The complete verification string
- **GmailMxRecordOutput**: Domain name of the MX record

## Prerequisites and Requirements

### System Dependencies

- **Python 3.8+**: Required for AWS CDK Python applications
- **Node.js 18+**: Required by AWS CDK CLI
- **Git**: For cloning and version control

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```txt
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[route53,route53domains,account,organizations]>=1.34.0
```

### AWS Prerequisites

- **AWS Account**: Valid AWS account with appropriate permissions
- **Route 53 Hosted Zone**: Pre-existing hosted zone for the domain
- **Cross-Stack References**: The hosted zone must export:
  - `{domain-name}-HostedZoneId`
  - `{domain-name}-HostedZoneName`

## Configuration

### config.json

The main configuration file contains:

```json
{
  "aws": {
    "account_id": 781581267945,
    "bedrock": {
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "region": "us-east-1"
  },
  "domain_name": "10ulabs.com",
  "google_site_verification": "vkFVA-Ru1PwnePtOWeOt0k5bmzOpHtjfDZU-PfUKjRM",
  "ttl": 300
}
```

#### Configuration Parameters

| Parameter | Description | Required |
| --------- | ----------- | -------- |
| `aws.account_id` | AWS account ID for deployment | Yes |
| `aws.region` | AWS region for resources | Yes |
| `domain_name` | Domain name for email configuration | Yes |
| `google_site_verification` | Google verification token | Yes |
| `ttl` | DNS record TTL in seconds | No (default: 300) |

### cdk.json

CDK configuration with feature flags and context settings:

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/__pycache__",
      "**/.pytest_cache",
      ".git"
    ]
  }
}
```

## Usage Instructions

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd gmail-email-provider
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI**:

   ```bash
   npm install -g aws-cdk
   ```

4. **Configure AWS credentials**:

   ```bash
   aws configure
   # or use environment variables, IAM roles, etc.
   ```

### Deployment

1. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap aws://781581267945/us-east-1
   ```

2. **Review the deployment**:

   ```bash
   cdk diff
   ```

3. **Deploy the infrastructure**:

   ```bash
   cdk deploy
   ```

4. **View outputs**:

   ```bash
   cdk output
   ```

### Verification

After deployment, verify the DNS records:

1. **Check MX record**:

   ```bash
   dig MX 10ulabs.com
   ```

2. **Check TXT record**:

   ```bash
   dig TXT 10ulabs.com
   ```

3. **Verify in Google Search Console**:
   - Add the domain to Google Search Console
   - Use the DNS verification method
   - Confirm ownership using the created TXT record

## Architecture Overview

### Component Interaction

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gmail SMTP    │    │   Route 53      │    │  Domain Owners  │
│   Servers       │◄───┤   DNS Records   ├───►│  & Email Users  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Google Site     │
                       │ Verification    │
                       └─────────────────┘
```

### DNS Flow

1. **Email Routing**: MX record directs email to `smtp.google.com`
2. **Domain Verification**: TXT record proves domain ownership to Google
3. **Cross-Stack Integration**: Imports hosted zone from existing stack

### Dependencies

- **Hosted Zone Stack**: Must exist before deployment
- **Export Values**: Required for cross-stack references
- **DNS Propagation**: Records may take time to propagate globally

## Security Considerations

### DNS Security

- **Record Integrity**: Use short TTL during initial setup for quick changes
- **Access Control**: Limit Route 53 permissions to authorized users only
- **Monitoring**: Monitor DNS changes through CloudTrail

### Configuration Security

- **Sensitive Data**: Google verification token is public but domain-specific
- **Account ID**: Exposed in config but required for CDK deployment
- **Cross-Stack References**: Ensure source stack exports are secure

### Best Practices

- **Version Control**: Keep configuration in version control
- **Environment Separation**: Use different configs for different environments
- **Regular Audits**: Review DNS records and permissions regularly

## Troubleshooting

### Common Issues

**ImportValue Error**:

```text
Export {domain-name}-HostedZoneId cannot be found
```

- **Solution**: Ensure the hosted zone stack is deployed first
- **Check**: Verify export names match the expected format

**DNS Propagation Delays**:

- **Wait Time**: DNS changes can take up to 48 hours to propagate
- **Check Tools**: Use online DNS checkers from different locations
- **TTL Impact**: Lower TTL values propagate faster but increase query load

**Google Verification Fails**:

- **Record Check**: Verify TXT record exists and has correct value
- **Format**: Ensure format is exactly `google-site-verification=TOKEN`
- **Propagation**: Wait for DNS propagation before verifying in Google

### Debugging Commands

1. **Check stack status**:

   ```bash
   cdk ls
   cdk diff
   ```

2. **View CloudFormation events**:

   ```bash
   aws cloudformation describe-stack-events \
     --stack-name GmailEmailProvider
   ```

3. **Test DNS resolution**:

   ```bash
   nslookup -type=MX 10ulabs.com
   nslookup -type=TXT 10ulabs.com
   ```

4. **Validate configuration**:

   ```bash
   python3 -c "import json; print(json.load(open('config.json')))"
   ```
