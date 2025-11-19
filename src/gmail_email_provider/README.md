# Gmail Email Provider CDK Stack

A comprehensive AWS CDK infrastructure-as-code solution for configuring Gmail as an email provider for custom domains. This stack automatically creates the necessary DNS records in Route53 to enable Gmail email services for your domain.

## Overview

This CDK stack configures DNS records required to use Gmail as your domain's email provider by creating:

- **Google Site Verification TXT Record**: Verifies domain ownership with Google
- **Gmail MX Record**: Routes email traffic through Google's SMTP servers (`smtp.google.com`)

The stack integrates with existing Route53 hosted zones and provides CloudFormation outputs for monitoring and verification.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK App       │───▶│  Gmail Provider  │───▶│   Route53       │
│   (app.py)      │    │  Stack           │    │   DNS Records   │
└─────────────────┘    │  (stack.py)      │    └─────────────────┘
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  CloudFormation  │
                       │  Outputs         │
                       └──────────────────┘
```

## Prerequisites

- **AWS CLI** configured with appropriate permissions
- **AWS CDK** v2.225.0 or later
- **Python** 3.8 or later
- **Route53 Hosted Zone** already created for your domain
- **Google Workspace** or Gmail account configured for custom domain
- **Domain verification token** from Google

### Required AWS Permissions

- `route53:GetHostedZone`
- `route53:ListResourceRecordSets`
- `route53:ChangeResourceRecordSets`
- `cloudformation:*` (for CDK operations)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd gmail-email-provider
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Update config.json

Edit the `config.json` file with your specific values:

```json
{
  "aws": {
    "account_id": "YOUR_AWS_ACCOUNT_ID",
    "region": "us-east-1"
  },
  "domain_name": "yourdomain.com",
  "google_site_verification": "YOUR_GOOGLE_VERIFICATION_TOKEN",
  "ttl": 300
}
```

**Configuration Parameters:**

- `aws.account_id`: Your AWS account ID (numeric)
- `aws.region`: AWS region where Route53 hosted zone exists
- `domain_name`: Your custom domain name
- `google_site_verification`: Google domain verification token (without the `google-site-verification=` prefix)
- `ttl`: DNS record TTL in seconds (default: 300)

### 2. Obtain Google Verification Token

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add your domain property
3. Choose "HTML tag" verification method
4. Extract the token from the meta tag content

### 3. Ensure Hosted Zone Dependencies

This stack imports an existing Route53 hosted zone using CloudFormation exports. Ensure your domain stack exports:

- `{domain-name-with-dashes}-HostedZoneId`
- `{domain-name-with-dashes}-HostedZoneName`

Example: For `example.com`, exports would be `example-com-HostedZoneId` and `example-com-HostedZoneName`.

## Deployment

### 1. Bootstrap CDK (first time only)

```bash
cdk bootstrap
```

### 2. Review changes

```bash
cdk diff
```

### 3. Deploy the stack

```bash
cdk deploy
```

### 4. Verify deployment

```bash
# Check CloudFormation outputs
aws cloudformation describe-stacks --stack-name GmailEmailProvider

# Verify DNS records
dig TXT yourdomain.com
dig MX yourdomain.com
```

## DNS Records Created

### TXT Record (Google Site Verification)
```
yourdomain.com.    300    IN    TXT    "google-site-verification=YOUR_TOKEN"
```

### MX Record (Gmail Mail Exchange)
```
yourdomain.com.    300    IN    MX     1 smtp.google.com.
```

## Testing

The project includes comprehensive tests at multiple levels:

### Unit Tests
```bash
# Test configuration and stack construction
pytest test/gmail_email_provider/test_unit.py -v
```

### Integration Tests
```bash
# Test deployed AWS resources
pytest test/gmail_email_provider/test_integration.py -v
```

### End-to-End Tests
```bash
# Test actual DNS resolution
pytest test/gmail_email_provider/test_e2e.py -v
```

### Run All Tests
```bash
pytest test/gmail_email_provider/ -v
```

## CloudFormation Outputs

The stack provides the following outputs for monitoring and verification:

| Output Key | Description |
|------------|-------------|
| `GoogleVerificationRecord` | FQDN of the Google verification TXT record |
| `GoogleVerificationValue` | Complete Google verification string |
| `GmailMxRecordOutput` | FQDN of the Gmail MX record |

## Troubleshooting

### Common Issues

**1. Import value not found error**
```
Export {domain}-HostedZoneId cannot be imported
```
- **Solution**: Ensure the domain stack has been deployed and exports the required values

**2. Google verification failing**
```
Site verification failed in Google Search Console
```
- **Solution**: Wait for DNS propagation (up to 48 hours) and verify the TXT record exists

**3. Email not routing to Gmail**
```
Emails bouncing or not received
```
- **Solution**: Verify MX record is correctly set and Gmail is configured for the domain

### Verification Commands

```bash
# Check DNS propagation
nslookup -type=TXT yourdomain.com
nslookup -type=MX yourdomain.com

# Test with different DNS servers
nslookup -type=MX yourdomain.com 8.8.8.8

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name GmailEmailProvider --query 'Stacks[0].StackStatus'
```

## CDK Commands

| Command | Description |
|---------|-------------|
| `cdk list` | List all stacks |
| `cdk synth` | Generate CloudFormation template |
| `cdk diff` | Compare deployed stack with current state |
| `cdk deploy` | Deploy the stack |
| `cdk destroy` | Delete the stack |
| `cdk watch` | Watch for changes and auto-deploy |

## Monitoring

### AWS Resources to Monitor

- **Route53 Records**: Verify TXT and MX records exist
- **CloudFormation Stack**: Monitor stack status and events
- **DNS Query Logs**: Enable Route53 query logging if needed

### Health Checks

```bash
# Automated health check script
#!/bin/bash
DOMAIN="yourdomain.com"

echo "Checking TXT record..."
dig +short TXT $DOMAIN | grep "google-site-verification"

echo "Checking MX record..."
dig +short MX $DOMAIN | grep "smtp.google.com"
```

## Security Considerations

- DNS records are publicly visible
- TTL values affect propagation time vs. flexibility
- Ensure Google Workspace security settings are properly configured
- Monitor for unauthorized DNS changes

## Contributing

When contributing to this project:

1. Run all tests: `pytest test/gmail_email_provider/ -v`
2. Update configuration examples if needed
3. Test deployment in a non-production environment
4. Document any new configuration options
