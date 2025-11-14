# Gmail Email Provider Stack

This AWS CDK stack configures Gmail as an email provider for your custom domain
through DNS verification. It sets up the necessary Route53 DNS records to
enable Gmail to send and receive emails for your domain.

## Overview

The Gmail Email Provider Stack automates the DNS configuration required to use
Gmail with a custom domain. It creates the essential DNS records for Google
site verification and Gmail MX routing, ensuring proper email delivery and
domain ownership verification.

## Key Features

- **Automated DNS Configuration**: Creates required TXT and MX records
- **Cross-Stack Integration**: Imports hosted zone from existing domain stack
- **Configurable TTL**: Customizable DNS record time-to-live values
- **Validation**: Ensures required configuration parameters are present
- **CloudFormation Outputs**: Provides verification details for monitoring

## Resources Created

This stack creates the following AWS resources:

### Route53 DNS Records

- **TXT Record**: Google site verification record for domain ownership
- **MX Record**: Gmail mail exchange record pointing to `smtp.google.com`

### Imported Resources

The stack imports an existing Route53 hosted zone using CloudFormation
cross-stack references:

- Hosted Zone ID from `{domain-name}-HostedZoneId` export
- Hosted Zone Name from `{domain-name}-HostedZoneName` export

## Prerequisites

Before deploying this stack, ensure you have:

1. **Existing Domain Stack**: A deployed domain stack that exports:
   - Hosted Zone ID
   - Hosted Zone Name

2. **Google Site Verification Code**: Obtained from Google Search Console
   or Google Workspace admin console

3. **AWS CDK**: Version 2.x installed and configured

4. **AWS Credentials**: Properly configured with Route53 permissions

5. **Python Dependencies**: AWS CDK Python libraries installed

## Configuration

Create a configuration dictionary with the following parameters:

```python
config = {
    "domain_name": "example.com",
    "google_site_verification": "your-verification-code-here",
    "ttl": 300  # Optional, defaults to 300 seconds
}
```

### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_name` | string | Yes | Your custom domain name |
| `google_site_verification` | string | Yes | Google verification code |
| `ttl` | integer | No | DNS record TTL (default: 300) |

## Usage Instructions

### Step 1: Obtain Google Verification Code

1. Go to Google Search Console or Google Workspace admin console
2. Add your domain for verification
3. Choose "HTML tag" verification method
4. Copy the verification code from the meta tag content

### Step 2: Deploy the Stack

```python
from aws_cdk import App
from stack import GmailEmailProviderStack

app = App()

config = {
    "domain_name": "yourdomain.com",
    "google_site_verification": "abcd1234efgh5678",
    "ttl": 300
}

GmailEmailProviderStack(
    app, 
    "GmailEmailProviderStack",
    config=config,
    env={"region": "us-east-1"}
)

app.synth()
```

### Step 3: Deploy Using CDK CLI

```bash
# Install dependencies
npm install -g aws-cdk
pip install aws-cdk-lib constructs

# Deploy the stack
cdk deploy GmailEmailProviderStack
```

## Architecture

### DNS Verification Process

1. **Domain Ownership**: Google requires TXT record verification to confirm
   domain ownership
2. **Mail Routing**: MX record directs email traffic to Gmail servers
3. **Cross-Stack Dependencies**: Hosted zone imported from domain stack

### Stack Dependencies

```text
Domain Stack (creates hosted zone)
    ↓ (exports hosted zone details)
Gmail Provider Stack (imports hosted zone)
    ↓ (creates DNS records)
Google Services (verifies domain)
```

### CloudFormation Cross-Stack References

The stack uses CloudFormation exports/imports for loose coupling:

- **Export Format**: `{domain-with-dashes}-HostedZoneId`
- **Import Function**: `Fn.import_value()` for dynamic references
- **Benefits**: Allows independent stack lifecycle management

## Testing and Verification

### Verify DNS Records

```bash
# Check TXT record
dig TXT yourdomain.com

# Check MX record
dig MX yourdomain.com

# Verify with Google's tool
nslookup -type=TXT yourdomain.com
```

### Google Verification

1. Return to Google Search Console or Workspace admin
2. Click "Verify" button for your domain
3. Confirmation should appear within minutes

### Email Testing

After Gmail configuration in Google Workspace:

1. Send test email from Gmail interface
2. Verify email headers show your custom domain
3. Test receiving emails at your custom domain addresses

## Security Considerations

### DNS Security

- **Record Integrity**: DNS records are publicly visible
- **TTL Values**: Lower TTL allows faster changes but increases DNS queries
- **Zone Access**: Ensure hosted zone has appropriate access controls

### Google Integration

- **Verification Code**: Keep verification codes secure and rotate if needed
- **Domain Control**: Only verified domain owners can modify DNS records
- **Email Security**: Configure SPF, DKIM, and DMARC records for full security

## Troubleshooting

### Common Issues

#### Stack Deployment Fails

```bash
# Check if domain stack exports exist
aws cloudformation list-exports --query 'Exports[?Name==`yourdomain-com-HostedZoneId`]'
```

#### Google Verification Fails

1. **DNS Propagation**: Wait 24-48 hours for global DNS propagation
2. **Record Format**: Ensure TXT record exactly matches Google's requirement
3. **Multiple Records**: Check for conflicting TXT records

#### Email Delivery Issues

1. **MX Priority**: Verify MX record has priority 1
2. **Gmail Setup**: Complete Gmail configuration in Google Workspace
3. **Additional Records**: Configure SPF, DKIM, DMARC for deliverability

### Debugging Commands

```bash
# Check CloudFormation exports
aws cloudformation describe-stacks --stack-name YourDomainStack

# Verify DNS propagation
dig @8.8.8.8 TXT yourdomain.com
dig @1.1.1.1 MX yourdomain.com

# Check stack outputs
aws cloudformation describe-stacks --stack-name GmailEmailProviderStack
```

### Stack Rollback

If deployment fails, CDK automatically rolls back. To manually clean up:

```bash
# Delete the stack
cdk destroy GmailEmailProviderStack

# Check for remaining resources
aws route53 list-resource-record-sets --hosted-zone-id YOUR-ZONE-ID
```

## Monitoring and Maintenance

### CloudFormation Outputs

The stack provides outputs for monitoring:

- **GoogleVerificationRecord**: DNS name of verification record
- **GoogleVerificationValue**: Verification string value
- **GmailMxRecordOutput**: DNS name of MX record

### Maintenance Tasks

- **Verification Renewal**: Google verification typically doesn't expire
- **DNS Monitoring**: Monitor DNS record integrity
- **Stack Updates**: Update TTL or configuration as needed