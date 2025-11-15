# Gmail Email Provider DNS Configuration

This AWS CDK infrastructure project configures DNS records for Gmail email
services on the 10ulabs.com domain. It creates the necessary Route53 records
to enable Gmail as the email provider, including MX records for mail routing
and Google site verification records.

## Purpose and Key Features

- **Gmail Integration**: Configures DNS records to use Gmail as the email
  provider for a custom domain
- **Google Site Verification**: Creates TXT records for Google domain
  ownership verification
- **Route53 Management**: Manages DNS records through AWS Route53 hosted zones
- **Infrastructure as Code**: Uses AWS CDK for reproducible DNS configuration
- **Cross-Stack Integration**: Imports existing hosted zone from another stack

## Resources Created

This infrastructure creates the following AWS resources:

- **Route53 TXT Record**: Google site verification record with configurable
  verification token
- **Route53 MX Record**: Mail exchange record pointing to `smtp.google.com`
  with priority 1
- **CloudFormation Outputs**: Exposes created record information for
  reference

## Prerequisites and Requirements

### Python Dependencies

```txt
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[route53,route53domains,account,organizations]>=1.34.0
```

### System Dependencies

- **Python 3.7+**: Required for AWS CDK Python bindings
- **Node.js 14+**: Required for AWS CDK CLI and core functionality
- **Git**: Required for version control and CDK operations

### AWS Prerequisites

- AWS account with appropriate permissions for Route53 operations
- Existing Route53 hosted zone for the target domain
- The hosted zone must export its ID and name as CloudFormation outputs

## Configuration

### config.json Structure

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000,
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
| --------- | ----------- | -------- |
| `aws.account_id` | AWS account ID for deployment | Yes |
| `aws.region` | AWS region for resources | Yes |
| `domain_name` | Target domain for email configuration | Yes |
| `google_site_verification` | Google verification token | Yes |
| `ttl` | DNS record TTL in seconds | No (default: 300) |

### CDK Configuration

The `cdk.json` file includes watch mode configuration and CDK feature flags
for consistent behavior across deployments.

## Usage Instructions

### Installation

1. Clone the repository and navigate to the project directory

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK CLI globally:

   ```bash
   npm install -g aws-cdk
   ```

4. Configure AWS credentials using boto3 (environment variables, AWS config
   files, or IAM roles)

### Deployment

1. Verify CDK configuration:

   ```bash
   cdk doctor
   ```

2. Synthesize the CloudFormation template:

   ```bash
   cdk synth
   ```

3. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

4. Confirm the deployment when prompted

### Verification

After deployment, verify the DNS records:

```bash
# Check MX record
dig MX 10ulabs.com

# Check Google verification TXT record
dig TXT 10ulabs.com
```

## Architecture Overview

### Component Interactions

1. **CDK App Entry Point**: `app.py` loads configuration and initializes the
   stack
2. **Stack Definition**: `stack.py` defines Route53 resources and their
   relationships
3. **Hosted Zone Import**: References existing hosted zone via CloudFormation
   exports
4. **DNS Record Creation**: Creates MX and TXT records within the imported
   hosted zone

### DNS Configuration Flow

```text
Gmail SMTP (smtp.google.com)
            ↑
    MX Record (Priority 1)
            ↑
    Route53 Hosted Zone
            ↑
    CloudFormation Stack
```

### Cross-Stack Dependencies

The stack imports the hosted zone using CloudFormation exports with the
naming convention:

- Hosted Zone ID: `{domain-name-with-dashes}-HostedZoneId`
- Hosted Zone Name: `{domain-name-with-dashes}-HostedZoneName`

For `10ulabs.com`, this translates to:

- `10ulabs-com-HostedZoneId`
- `10ulabs-com-HostedZoneName`

## Security Considerations

### DNS Security

- **Record Integrity**: DNS records are managed through Infrastructure as
  Code, preventing manual configuration drift
- **Access Control**: Route53 operations require appropriate IAM permissions
- **Domain Ownership**: Google site verification ensures domain ownership
  before enabling services

### Email Security

- **MX Record Security**: Points only to Google's official SMTP servers
- **TTL Configuration**: Uses reasonable TTL values to balance caching and
  update flexibility

### AWS Security

- **Least Privilege**: CDK deployment requires only necessary Route53
  permissions
- **Resource Tagging**: All resources are tagged for management and cost
  tracking

## Troubleshooting

### Common Issues

**Hosted Zone Import Fails**

```text
Error: Cannot import value {domain}-HostedZoneId
```

- Verify the source hosted zone stack is deployed
- Check that CloudFormation exports exist with correct naming
- Confirm the domain name format matches the export naming convention

**Google Verification Fails**

```text
Error: Domain ownership not verified
```

- Verify the `google_site_verification` token in `config.json`
- Check DNS propagation using `dig TXT {domain}`
- Ensure the TXT record value includes the `google-site-verification=` prefix

**MX Record Not Working**

```text
Error: Mail delivery fails
```

- Verify MX record points to `smtp.google.com.` (note the trailing dot)
- Check MX record priority is set to 1
- Confirm Gmail workspace is configured for the domain

### Debugging Commands

```bash
# Check CloudFormation exports
aws cloudformation list-exports --query "Exports[?Name=='10ulabs-com-HostedZoneId']"

# Verify DNS propagation
dig MX 10ulabs.com @8.8.8.8
dig TXT 10ulabs.com @8.8.8.8

# Check CDK differences
cdk diff

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name GmailEmailProvider
```

### DNS Propagation

DNS changes may take up to 48 hours to propagate globally. Use multiple DNS
servers to verify propagation status:

```bash
# Check different DNS servers
dig MX 10ulabs.com @8.8.8.8        # Google DNS
dig MX 10ulabs.com @1.1.1.1        # Cloudflare DNS  
dig MX 10ulabs.com @208.67.222.222  # OpenDNS
```
