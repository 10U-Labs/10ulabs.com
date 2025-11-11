# Gmail Email Provider AWS CDK Stack

## Overview

This AWS CDK infrastructure code provisions DNS records required to configure Gmail as an email provider for a custom domain. It automates the setup of DNS verification records through Route53, enabling email services via Gmail's infrastructure while maintaining your custom domain identity.

## Purpose and Key Features

This stack handles the DNS-level configuration necessary for Gmail email provider integration:

- **Google Site Verification**: Creates a TXT record for domain ownership verification
- **MX Record Configuration**: Sets up Mail Exchange records pointing to Gmail's servers
- **Cross-Stack Integration**: Imports hosted zone information from a parent domain stack
- **Automated DNS Management**: Eliminates manual DNS record creation and reduces configuration errors
- **Environment Flexibility**: Supports multiple domains through configurable parameters

## Resources Created

### Route53 Records

1. **Google Site Verification TXT Record**
   - Type: TXT
   - Value: `google-site-verification={verification-code}`
   - Purpose: Proves domain ownership to Google services
   - TTL: Configurable (default: 300 seconds)

2. **Gmail MX Record**
   - Type: MX
   - Priority: 1
   - Host: `smtp.google.com.`
   - Purpose: Routes email traffic to Gmail's SMTP servers

### Cross-Stack References

The stack imports the following resources from a parent domain stack via CloudFormation exports:
- `{domain-name-with-hyphens}-HostedZoneId`: The Route53 hosted zone identifier
- `{domain-name-with-hyphens}-HostedZoneName`: The Route53 hosted zone name

## Prerequisites and Requirements

### AWS Account and Permissions

- AWS account with appropriate IAM permissions for:
  - Route53 record creation and management
  - CloudFormation stack operations
  - Importing cross-stack references

### Domain Setup

- Custom domain registered and configured in Route53
- Parent domain stack already deployed (exports hosted zone information)
- DNS nameservers pointing to the Route53 hosted zone

### Google/Gmail Requirements

- Active Google Workspace or Gmail account
- Google Site Verification code obtained from Google Search Console
- Access to Gmail's SMTP configuration

### Software Requirements

- Python 3.9+
- AWS CDK v2.x or later
- AWS CLI configured with appropriate credentials
- boto3 library

## Usage Instructions

### Installation

1. **Install Dependencies**
   ```bash
   pip install aws-cdk-lib constructs
   ```

2. **Set Up AWS Credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, default region, and output format
   ```

### Configuration

Create a `config.json` file with your domain and verification details:

```json
{
  "domain_name": "example.com",
  "google_site_verification": "your-verification-code-here",
  "ttl": 300
}
```

### Deployment

1. **Load Configuration**
   ```python
   import json
   with open('config.json') as f:
       config = json.load(f)
   ```

2. **Initialize Stack in App**
   ```python
   from aws_cdk import App
   from stack import GmailEmailProviderStack

   app = App()
   gmail_stack = GmailEmailProviderStack(
       app, 
       "GmailEmailProviderStack",
       config=config,
       env={
           "account": "YOUR_ACCOUNT_ID",
           "region": "us-east-1"
       }
   )
   app.synth()
   ```

3. **Deploy to AWS**
   ```bash
   cdk deploy
   ```

4. **Confirm Changes**
   - Review the CloudFormation changeset
   - Type `y` to proceed with deployment

### Verification

After deployment, verify DNS records are created:

```bash
# Check TXT record
dig example.com TXT

# Check MX record
dig example.com MX

# Or use nslookup
nslookup -type=MX example.com
nslookup -type=TXT example.com
```

## Architecture Explanation

### DNS Verification Flow

```
┌─────────────────────────────────────────────────────────┐
│  Gmail Email Provider Stack (This Stack)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Imports Hosted Zone via CloudFormation Exports   │   │
│  │ • HostedZoneId                                   │   │
│  │ • HostedZoneName                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Creates DNS Records in Route53                   │   │
│  │ • TXT: google-site-verification={code}           │   │
│  │ • MX:  priority=1, host=smtp.google.com.         │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
└──────────────────────────┼───────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
         Google Services         Gmail SMTP Servers
         (Verify Domain)         (Email Delivery)
```

### Stack Dependencies

**Cross-Stack Reference Model:**

```
Parent Domain Stack (Exports)
├── {domain}-HostedZoneId
└── {domain}-HostedZoneName
        │
        ▼
Gmail Email Provider Stack (Imports)
├── Creates TXT verification record
└── Creates MX routing record
```

This design pattern allows:
- **Separation of Concerns**: Domain infrastructure separate from email configuration
- **Reusability**: Single domain stack supports multiple email provider configurations
- **Flexibility**: Easy to add additional email providers without modifying domain stack

### CloudFormation Cross-Stack References

The stack uses `Fn.import_value()` to retrieve exported values from the parent domain stack:

```python
hosted_zone_id = Fn.import_value(f"{export_prefix}-HostedZoneId")
hosted_zone_name = Fn.import_value(f"{export_prefix}-HostedZoneName")
```

The domain name is transformed to create valid export names:
- `example.com` → `example-com-HostedZoneId`
- `mail.example.com` → `mail-example-com-HostedZoneName`

## Configuration Details

### Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_name` | String | Yes | - | Your custom domain (e.g., "example.com") |
| `google_site_verification` | String | Yes | - | Verification code from Google Search Console |
| `ttl` | Integer | No | 300 | DNS TTL in seconds |

### Obtaining Google Site Verification Code

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add your property (domain)
3. Choose "TXT record" verification method
4. Copy the verification string (alphanumeric code after `google-site-verification=`)
5. Add to `config.json` without the `google-site-verification=` prefix

**Example:**
```
If Google provides: google-site-verification=abc123xyz456
Your config value: abc123xyz456
```

### TTL Configuration

- **Lower TTL (60-300 seconds)**: Faster DNS propagation updates, higher query load
- **Higher TTL (3600+ seconds)**: Reduced DNS queries, slower update propagation
- **Recommended**: 300-900 seconds for email infrastructure

## Testing Approach

### Pre-Deployment Validation

1. **Verify Configuration File**
   ```bash
   cat config.json | python -m json.tool
   ```

2. **Validate Stack Syntax**
   ```bash
   cdk synth
   ```

3. **Check CloudFormation Template**
   ```bash
   cat cdk.out/GmailEmailProviderStack.template.json | python -m json.tool
   ```

### Post-Deployment Testing

1. **Verify DNS Records Propagate**
   ```bash
   # Wait 5 minutes for DNS propagation
   sleep 300
   
   # Check TXT record
   dig @8.8.8.8 example.com TXT | grep google-site-verification
   
   # Check MX record
   dig @8.8.8.8 example.com MX
   ```

2. **Use Google's Verification Tool**
   - Visit [Google Search Console](https://search.google.com/search-console)
   - Click "Verify" next to your property
   - Google will check the TXT record

3. **Test Gmail MX Records**
   ```bash
   # MX record should return priority 1 with smtp.google.com
   nslookup -type=MX example.com
   ```

4. **Email Delivery Test**
   - Send test email to user@example.com
   - Verify receipt and proper routing

### CloudFormation Validation

```bash
# View stack outputs
aws cloudformation describe-stacks \
  --stack-name GmailEmailProviderStack \
  --query 'Stacks[0].Outputs'

# View stack resources
aws cloudformation describe-stack-resources \
  --stack-name GmailEmailProviderStack
```

## Security Considerations

### DNS Security Best Practices

1. **Record Validation**
   - Verify TXT record values match Google's requirements exactly
   - MX record priority must be appropriate for your infrastructure
   - Regularly audit DNS records for unauthorized changes

2. **Access Control**
   - Restrict Route53 modifications to authorized personnel
   - Use IAM policies to limit DNS management permissions
   - Enable CloudTrail logging for all DNS modifications

   ```json
   {
     "Effect": "Allow",
     "Action": [
       "route53:ChangeResourceRecordSets",
       "route53:GetHostedZone"
     ],
     "Resource": [
       "arn:aws:route53:::hostedzone/HOSTED_ZONE_ID"
     ]
   }
   ```

3. **Verification Code Protection**
   - Store `google_site_verification` in AWS Secrets Manager or Parameter Store, not in version control
   - Never commit `config.json` to public repositories
   - Add to `.gitignore`:
     ```
     config.json
     config.*.json
     ```

### Email Security

1. **DMARC Configuration** (Recommended additional setup)
   - Add DMARC policy TXT record to prevent email spoofing
   - Format: `v=DMARC1; p=reject; rua=mailto:admin@example.com`

2. **SPF Records** (Recommended additional setup)
   - Add SPF record: `v=spf1 include:_spf.google.com ~all`
   - Specifies which servers can send email for your domain

3. **DKIM Records** (Recommended additional setup)
   - Gmail automatically signs emails; add DKIM public key to DNS
   - Enhances email authentication and deliverability

### Stack Security

- All resources created in your VPC account
- No data exposure through CloudFormation outputs
- DNS changes logged in CloudTrail
- Use cross-account roles if needed for multi-account deployments

## Troubleshooting Tips

### Common Issues and Solutions

#### 1. Import Value Not Found

**Error:** `Cross stack reference HostedZoneId not found`

**Causes and Solutions:**
```bash
# Verify parent stack is deployed
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE

# Check exported values
aws cloudformation list-exports \
  --query 'Exports[?Name==`example-com-HostedZoneId`]'

# Solution: Deploy parent domain stack first
cdk deploy DomainStack
```

**Domain name transformation check:**
- `example.com` should export `example-com-HostedZoneId`
- `mail.example.org` should export `mail-example-org-HostedZoneId`

#### 2. DNS Records Not Propagating

**Symptoms:** Records don't appear in DNS queries

**Solutions:**
```bash
# Clear local DNS cache (macOS)
sudo dscacheutil -flushcache

# Verify record in Route53
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --query 'ResourceRecordSets[?Type==`TXT`]'

# Check propagation globally
dig @1.1.1.1 example.com TXT
dig @8.8.8.8 example.com TXT
```

**Typical resolution time:** 5-15 minutes

#### 3. Google Verification Fails

**Symptoms:** Google Search Console says verification record not found

**Verification checklist:**
```bash
# 1. Confirm exact TXT record value
dig example.com TXT +short

# 2. Should output exactly:
# "google-site-verification=abc123xyz456"

# 3. If missing prefix, update config and redeploy
cdk deploy

# 4. Google typically rechecks every few minutes
# Wait 5-10 minutes before retrying verification
```

#### 4. CloudFormation Stack Creation Fails

**Error:** `User: arn:aws:iam::... is not authorized to perform: route53:ChangeResourceRecordSets`

**Solution:** Ensure IAM user/role has permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:*",
        "cloudformation:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 5. MX Record Priority Issues

**Symptoms:** Email not routing correctly

**Check current MX records:**
```bash
dig example.com MX +short

# Should show:
# 1 smtp.google.com.
```

**If incorrect, update and redeploy:**
```bash
# Modify config.json and redeploy
cdk deploy

# Verify changes
aws route53 list-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --query 'ResourceRecordSets[?Type==`MX`]'
```

#### 6. Configuration Validation Errors

**Error:** `google_site_verification is required in config`

**Solution:**
```python
# Verify config.json format
{
  "domain_name": "example.com",
  "google_site_verification": "your-code-here",  # Required!
  "ttl": 300
}

# Ensure no typos in key names
```

#### 7. Stack Update/Deletion Issues

**To update TTL or verification code:**
```bash
# Modify config.json
# Redeploy
cdk deploy

# View changes
cdk diff
```

**To delete the stack:**
```bash
# Review what will be deleted
cdk destroy

# Confirm deletion
# Note: DNS records will be removed, email may stop working
```

### Debug Commands

```bash
# View complete stack information
aws cloudformation describe-stacks \
  --stack-name GmailEmailProviderStack

# View stack events (deployment history)
aws cloudformation describe-stack-events \
  --stack-name GmailEmailProviderStack \
  --query 'StackEvents[0:10]'

# Validate template before deployment
cdk synth | aws cloudformation validate-template \
  --template-body file:///dev/stdin

# Check Route53 records in hosted zone
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC

# Monitor CDK deployment in verbose mode
cdk deploy --verbose --require-approval=never
```

### Contacting Support

If issues persist:

1. **Check AWS Status**: https://status.aws.amazon.com/
2. **Review CloudFormation Events**: Look for detailed error messages
3. **Check CDK Logs**: Review deployment output for specific failures
4. **Google Support**: For Gmail/Google Workspace verification issues
5. **AWS Support**: For Route53 or CloudFormation issues (requires support plan)

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Route53 DNS Records](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html)
- [Google Search Console](https://search.google.com/search-console)
- [Gmail for Business Setup](https://support.google.com/a/answer/9003945)
- [DNS Best Practices](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices.html)

## License

Specify your license here (e.g., MIT, Apache 2.0, etc.)