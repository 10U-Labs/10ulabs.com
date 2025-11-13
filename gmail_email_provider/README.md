# Gmail Email Provider CDK Stack

This AWS CDK stack configures Gmail as an email provider for a custom domain
through DNS verification. It creates the necessary Route53 DNS records to
enable Gmail services for your domain.

## Overview

The Gmail Email Provider Stack automates the DNS configuration required to
use Gmail (Google Workspace) with your custom domain. It sets up DNS
verification records and MX records to route email through Google's servers.

## Key Features

- **Automated DNS Configuration**: Creates required DNS records for Gmail
- **Google Site Verification**: Sets up TXT record for domain verification
- **MX Record Configuration**: Routes email traffic to Gmail servers
- **Cross-Stack Integration**: Imports hosted zone from existing domain stack
- **Configurable TTL**: Customizable DNS record time-to-live values

## Resources Created

### Route53 DNS Records

- **TXT Record**: Google site verification record for domain ownership proof
- **MX Record**: Mail exchange record pointing to Gmail servers

### Imported Resources

- **Hosted Zone**: Imports existing Route53 hosted zone via CloudFormation
  exports using the pattern `{domain-name}-HostedZoneId` and
  `{domain-name}-HostedZoneName`

## Prerequisites

### Required Infrastructure

1. **Existing Domain Stack**: A previously deployed stack that exports:
   - Hosted Zone ID as `{domain-name}-HostedZoneId`
   - Hosted Zone Name as `{domain-name}-HostedZoneName`

2. **Google Workspace Account**: Active Google Workspace or Gmail for
   Business account

3. **Domain Ownership**: Administrative access to your domain

### Required Tools

- AWS CLI configured with appropriate permissions
- AWS CDK v2.x installed
- Python 3.8 or higher
- Google Admin Console access

### Required Permissions

- `route53:ChangeResourceRecordSets`
- `route53:GetHostedZone`
- `route53:ListResourceRecordSets`
- `cloudformation:DescribeStacks`

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
| --- | --- | --- | --- |
| `domain_name` | string | Yes | Your custom domain name |
| `google_site_verification` | string | Yes | Google verification code |
| `ttl` | integer | No | DNS record TTL (default: 300) |

## Usage

### 1. Obtain Google Verification Code

1. Log into Google Admin Console
2. Navigate to "Domains" section
3. Add your domain and copy the verification code
4. The code looks like: `AbCdEfGhIjKlMnOpQrStUvWxYz123456789`

### 2. Deploy the Stack

```python
from aws_cdk import App
from stack import GmailEmailProviderStack

app = App()

config = {
    "domain_name": "yourdomain.com",
    "google_site_verification": "AbCdEfGhIjKlMnOpQrStUvWxYz123456789"
}

GmailEmailProviderStack(
    app,
    "GmailEmailProviderStack",
    config=config,
    env={"region": "us-east-1", "account": "123456789012"}
)

app.synth()
```

### 3. Deploy with CDK CLI

```bash
# Install dependencies
pip install aws-cdk-lib constructs

# Deploy the stack
cdk deploy GmailEmailProviderStack
```

## Architecture

### DNS Verification Flow

1. **Domain Verification**: Google requires proof of domain ownership through
   a TXT record containing a unique verification code
2. **Email Routing**: MX records direct email traffic to Gmail servers
3. **Cross-Stack Dependencies**: The stack imports hosted zone details from
   your existing domain infrastructure

### CloudFormation Cross-Stack References

The stack uses CloudFormation exports to reference existing infrastructure:

```python
# Imports from domain stack exports
hosted_zone_id = Fn.import_value(f"{export_prefix}-HostedZoneId")
hosted_zone_name = Fn.import_value(f"{export_prefix}-HostedZoneName")
```

### Gmail Integration Process

1. **Verification Record**: TXT record proves domain ownership to Google
2. **MX Record**: Routes email to `smtp.google.com` with priority 1
3. **Google Activation**: Once DNS propagates, Gmail services activate

## Testing

### Verify DNS Records

```bash
# Check TXT record
dig TXT yourdomain.com

# Check MX record
dig MX yourdomain.com

# Verify with specific DNS server
dig @8.8.8.8 MX yourdomain.com
```

### Expected DNS Results

```text
# TXT Record
yourdomain.com. 300 IN TXT "google-site-verification=AbCdEfGhIjKlMnOp..."

# MX Record
yourdomain.com. 300 IN MX 1 smtp.google.com.
```

### Google Verification Check

1. Return to Google Admin Console
2. Click "Verify Domain" button
3. Google will check DNS records automatically
4. Verification typically completes within minutes

## Security Considerations

### DNS Security

- **Record Integrity**: Ensure DNS records are not modified by unauthorized
  parties
- **TTL Values**: Lower TTL values allow faster updates but increase DNS query
  load
- **Access Control**: Limit Route53 permissions to necessary personnel

### Domain Verification

- **Verification Codes**: Keep Google verification codes confidential
- **Admin Access**: Restrict Google Admin Console access appropriately
- **Domain Ownership**: Verify domain ownership before adding verification
  records

## Troubleshooting

### Common Issues

#### DNS Propagation Delays

```bash
# Check multiple DNS servers
dig @8.8.8.8 TXT yourdomain.com
dig @1.1.1.1 TXT yourdomain.com
dig @208.67.222.222 TXT yourdomain.com
```

**Solution**: Wait 24-48 hours for full global DNS propagation

#### Missing CloudFormation Exports

**Error**: `Export {domain-name}-HostedZoneId cannot be imported`

**Solution**: Ensure your domain stack exports the required values:

```python
CfnOutput(
    self, "HostedZoneId",
    value=hosted_zone.hosted_zone_id,
    export_name=f"{export_prefix}-HostedZoneId"
)
```

#### Google Verification Failures

**Error**: "Domain verification failed"

**Solutions**:

1. Verify TXT record exists and contains correct verification code
2. Check for typos in verification code
3. Wait for DNS propagation (up to 48 hours)
4. Try verification from different geographic locations

#### Email Delivery Issues

**Error**: Emails not routing to Gmail

**Solutions**:

1. Verify MX record points to `smtp.google.com`
2. Check MX record priority is set to 1
3. Ensure Google Workspace is properly configured
4. Test email delivery with online MX record checkers

### Debug Commands

```bash
# Validate stack configuration
cdk diff GmailEmailProviderStack

# Check CloudFormation exports
aws cloudformation list-exports --region us-east-1

# Monitor stack deployment
aws cloudformation describe-stack-events \
  --stack-name GmailEmailProviderStack
```
