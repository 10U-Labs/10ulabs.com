# Gmail Email Provider Infrastructure with AWS CDK

## Overview

This AWS CDK infrastructure stack configures Gmail as an email provider for your domain by automating DNS verification through Route53. It creates a Google Site Verification TXT record in your hosted zone, enabling secure email delivery and Google service integration.

## Purpose and Key Features

- **Automated DNS Configuration**: Programmatically creates DNS TXT records required for Google site verification
- **Cross-Stack References**: Uses CloudFormation exports to reference an existing Route53 hosted zone
- **Google Integration Ready**: Enables Gmail services and Google Workspace integration for your domain
- **Configurable TTL**: Supports customizable DNS record time-to-live values
- **Infrastructure as Code**: Fully declarative infrastructure using AWS CDK with Python

## Resources Created

### Route53 TXT Record
- **Resource Type**: `AWS::Route53::RecordSet`
- **Purpose**: Stores Google site verification token for domain ownership verification
- **Format**: `google-site-verification=<verification-code>`
- **Hosted Zone**: Imported from existing hosted zone via CloudFormation cross-stack exports

### CloudFormation Exports Reference
The stack imports the following exports from a domain/hosted zone stack:
- `{domain-name}-HostedZoneId`: The Route53 hosted zone ID
- `{domain-name}-HostedZoneName`: The Route53 hosted zone name

## Prerequisites and Requirements

### AWS Resources
- An existing Route53 hosted zone for your domain
- A parent CDK stack that exports the hosted zone ID and name
- AWS credentials configured with appropriate IAM permissions

### Required IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:CreateResourceRecordSets",
        "route53:ListResourceRecordSets",
        "route53:GetHostedZone",
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DescribeStacks"
      ],
      "Resource": "*"
    }
  ]
}
```

### Software Requirements
- Python 3.8 or higher
- AWS CDK CLI (v2.0 or later)
- AWS CLI configured with appropriate credentials
- boto3 (for AWS interactions)

### Configuration Requirements
- Domain name matching the hosted zone
- Google Site Verification code from Google Search Console
- Parent stack that exports the hosted zone information

## Usage Instructions

### 1. Installation

Clone or download the infrastructure code and install dependencies:

```bash
# Install AWS CDK
npm install -g aws-cdk

# Install Python dependencies
pip install aws-cdk-lib constructs
```

### 2. Configuration

Create a configuration file or define the config dictionary with your domain and verification details:

```python
config = {
    "domain_name": "example.com",
    "google_site_verification": "your-verification-code-here",
    "ttl": 300  # Optional: defaults to 300 seconds
}
```

### 3. Stack Definition

Define the stack in your CDK app:

```python
from aws_cdk import App
from stack import GmailEmailProviderStack

app = App()

config = {
    "domain_name": "example.com",
    "google_site_verification": "abc123def456ghi789",
    "ttl": 300
}

email_stack = GmailEmailProviderStack(
    app, "GmailEmailProviderStack",
    config=config,
    env={
        "account": "123456789012",
        "region": "us-east-1"
    }
)

app.synth()
```

### 4. Deployment

Deploy the stack using AWS CDK:

```bash
# Synthesize CloudFormation template
cdk synth

# Review changes
cdk diff

# Deploy to AWS
cdk deploy

# Deploy with automatic approval (use with caution)
cdk deploy --require-approval never
```

### 5. Verification

After deployment, verify the DNS record:

```bash
# Query the TXT record
nslookup -type=TXT example.com

# Or using dig
dig TXT example.com

# Or using AWS CLI
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  --query "ResourceRecordSets[?Type=='TXT']"
```

## Architecture Explanation

### DNS Verification Flow for Gmail

```
┌─────────────────────────────────────────────────────────┐
│ Google Search Console                                   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ User enters domain: example.com                     │ │
│ │ Google generates verification code                  │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ AWS CDK Stack (This Infrastructure)                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 1. Import HostedZone from CloudFormation Export    │ │
│ │ 2. Create TXT Record with verification value       │ │
│ │ 3. Output record details                           │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Route53 Hosted Zone (example.com)                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TXT Record: google-site-verification=abc123...     │ │
│ │ TTL: 300 seconds                                    │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Google DNS Verification                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Google queries DNS: TXT record at example.com       │ │
│ │ Verifies: google-site-verification=abc123...       │ │
│ │ Status: ✓ Verified                                 │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Cross-Stack References

This stack uses CloudFormation **cross-stack exports** to reference an existing hosted zone:

```
Parent Stack (Domain Stack)
├── Route53 HostedZone
└── Exports:
    ├── "example-com-HostedZoneId" → Z123456789ABC
    └── "example-com-HostedZoneName" → example.com

                    ↓ (Fn.import_value)

Gmail Email Provider Stack
├── Imports hosted zone attributes
├── Creates TXT record
└── Outputs verification details
```

**Benefits:**
- Loose coupling between stacks
- Automated dependency resolution
- No manual zone ID/name copying required
- Supports multi-stack deployments

### Domain Name Export Convention

The stack uses a predictable naming convention for CloudFormation exports:
- Dots (`.`) in domain names are replaced with hyphens (`-`)
- Export format: `{sanitized-domain-name}-HostedZoneId` and `{sanitized-domain-name}-HostedZoneName`

Example: `example.com` → `example-com-HostedZoneId`

## Configuration Details

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `domain_name` | string | Your registered domain name | `example.com` |
| `google_site_verification` | string | Verification code from Google Search Console | `abc123def456ghi789` |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | integer | `300` | DNS record TTL in seconds |

### Configuration Example

```python
config = {
    # Required
    "domain_name": "mail.example.com",
    "google_site_verification": "verification_code_from_google_console",
    
    # Optional
    "ttl": 3600  # Keep record for 1 hour
}
```

### Obtaining Google Site Verification Code

1. Log in to [Google Search Console](https://search.google.com/search-console)
2. Add your property (domain)
3. Select "DNS record" verification method
4. Copy the provided verification code
5. Use this code in the `google_site_verification` configuration

## Testing Approach

### 1. Pre-Deployment Validation

```bash
# Validate CDK syntax
cdk synth

# Check for configuration errors
python -m py_compile stack.py

# Lint infrastructure code
pylint stack.py
```

### 2. DNS Record Verification

```bash
# Immediately after deployment
dig +short TXT example.com | grep google-site-verification

# Using nslookup
nslookup -type=TXT example.com 8.8.8.8

# Query Route53 directly
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  --query "ResourceRecordSets[?Name=='example.com.']"
```

### 3. Google Verification Confirmation

1. Go to Google Search Console
2. Navigate to the property settings
3. Click "Verify" to confirm DNS record
4. Google will confirm ownership within minutes

### 4. Integration Testing

```python
import boto3
from botocore.exceptions import ClientError

route53_client = boto3.client('route53')

def verify_txt_record(hosted_zone_id, domain_name):
    """Verify TXT record exists in Route53"""
    try:
        response = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=domain_name,
            StartRecordType='TXT'
        )
        
        for record in response['ResourceRecordSets']:
            if 'google-site-verification' in str(record.get('ResourceRecords', [])):
                return True
        return False
    except ClientError as e:
        print(f"Error verifying record: {e}")
        return False
```

## Security Considerations

### 1. Verification Code Protection
- Store verification codes in AWS Secrets Manager or Parameter Store, not in source code
- Never commit verification codes to version control
- Use environment variables or secure parameter passing

```python
import json
from aws_cdk import aws_secretsmanager

# Load config from Secrets Manager
secret = aws_secretsmanager.Secret.from_secret_name_v2(
    self, "GoogleVerification",
    secret_name="google-verification-secret"
)

config = json.loads(secret.secret_value.to_string())
```

### 2. IAM Permissions
- Apply principle of least privilege
- Restrict Route53 permissions to specific hosted zones
- Use resource-based policies when possible

```json
{
  "Effect": "Allow",
  "Action": "route53:*",
  "Resource": "arn:aws:route53:::hostedzone/Z123456789ABC"
}
```

### 3. DNS Security
- Enable DNSSEC for the hosted zone
- Implement DNS firewall rules
- Monitor DNS query logs

### 4. Access Control
- Restrict stack deployment permissions
- Enable CloudTrail logging for audit trails
- Use MFA for production deployments

### 5. Configuration Management
- Use AWS Systems Manager Parameter Store for configuration
- Implement configuration validation
- Version control infrastructure code only

## Troubleshooting Tips

### Issue: CloudFormation Export Not Found

**Error Message:**
```
Error: Unable to resolve cross-stack reference to export-name
```

**Solution:**
1. Verify the parent stack has been deployed
2. Check export names match exactly (case-sensitive)
3. Verify parent stack is in the same account and region
4. List available exports:
```bash
aws cloudformation list-exports --query "Exports[?Name=='example-com-HostedZoneId']"
```

### Issue: TXT Record Not Creating

**Error Message:**
```
Resource creation cancelled
```

**Solutions:**
- Verify hosted zone exists and is active
- Check IAM permissions for Route53
- Ensure domain name in config matches hosted zone exactly
- Verify TTL is a valid integer value

### Issue: DNS Record Not Resolving

**Symptoms:**
- `nslookup` returns no results
- Google verification fails
- Record shows in Route53 but doesn't resolve

**Solutions:**
1. Wait for DNS propagation (up to 48 hours, typically 5-30 minutes)
2. Force refresh DNS cache:
```bash
# macOS
sudo dscacheutil -flushcache

# Linux
sudo systemctl restart systemd-resolved

# Windows
ipconfig /flushdns
```
3. Check nameservers are correct:
```bash
dig NS example.com
```

### Issue: Google Verification Fails

**Symptoms:**
- Record exists but Google still can't verify
- Error: "Couldn't verify your ownership of example.com"

**Solutions:**
1. Verify exact verification code from Google
2. Ensure record format is exactly: `google-site-verification=CODE`
3. Check for trailing spaces in configuration
4. Wait 5-10 minutes for DNS propagation
5. Verify through Google Search Console again

### Issue: Imported HostedZone Attributes Error

**Error:**
```
Error: HostedZone.from_hosted_zone_attributes() received invalid zone_name
```

**Solution:**
- Ensure zone name has trailing dot: `example.com.`
- Verify export value format
- Check for special characters in domain name

### Issue: Stack Update Fails

**Error:**
```
User: arn:aws:iam::... is not authorized to perform: route53:ChangeResourceRecordSets
```

**Solution:**
- Verify IAM user/role has Route53 permissions
- Check resource-based policies on hosted zone
- Ensure CloudFormation service role has required permissions

### Debugging Commands

```bash
# View stack events
aws cloudformation describe-stack-events \
  --stack-name GmailEmailProviderStack

# Check CloudFormation exports
aws cloudformation list-exports

# Query Route53 directly
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABC

# Enable debug logging in CDK
cdk deploy --debug 2>&1 | tee deploy.log

# Validate CloudFormation template
aws cloudformation validate-template \
  --template-body file://cdk.out/template.json
```

## Best Practices

1. **Use Configuration Management**: Store sensitive data in AWS Secrets Manager
2. **Version Your Infrastructure**: Keep infrastructure code in Git with version tags
3. **Test Before Deployment**: Use `cdk diff` to preview changes
4. **Monitor DNS Changes**: Enable CloudTrail for audit logs
5. **Automate Verification**: Integrate verification checks into CI/CD pipelines
6. **Document Your Setup**: Maintain runbooks for DNS management
7. **Plan for Rollback**: Keep previous DNS configurations documented
8. **Regular Backups**: Export Route53 records periodically

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/v2/guide/)
- [Route53 User Guide](https://docs.aws.amazon.com/route53/)
- [Google Search Console Help](https://support.google.com/webmasters)
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [CloudFormation Cross-Stack References](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/walkthrough-crossstackref.html)