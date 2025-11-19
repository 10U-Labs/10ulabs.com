# 10ulabs.com Domain and CloudTrail Infrastructure

AWS CDK infrastructure for automating domain registration and CloudTrail setup for the 10ulabs.com domain. This stack provides foundational AWS resources including domain management, DNS hosting, and comprehensive audit logging.

## Overview

This CDK application automatically:
- Registers domains via Route53 Domains API if not already registered
- Creates and manages Route53 hosted zones
- Sets up multi-region CloudTrail for audit logging
- Configures secure S3 buckets with encryption and access logging
- Integrates with CloudWatch Logs for centralized logging
- Exports DNS resources for use by other stacks

## Architecture

### Core Components

- **Domain Registration Lambda**: Custom CloudFormation resource that handles domain registration and hosted zone setup
- **CloudTrail**: Multi-region trail capturing all AWS API calls with S3 and CloudWatch Logs integration
- **S3 Buckets**: Encrypted storage for CloudTrail logs with access logging to separate bucket
- **Route53 Hosted Zone**: Public DNS zone with nameserver exports for cross-stack references

### Security Features

- S3 buckets with encryption (AES256) and complete public access blocking
- Domain privacy protection enabled for all contact types
- SSL enforcement on S3 bucket policies
- CloudTrail logging all management events (read/write operations)
- CloudWatch Logs retention set to 1 year

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.8 or later
- Node.js 18.x or later (for CDK)
- AWS account with complete contact information configured

### Required AWS Permissions

The deployment requires permissions for:
- Route53 Domains (registration, domain details, operations)
- Route53 (hosted zones, DNS records)
- CloudTrail (trail creation and configuration)
- S3 (bucket creation, policies, encryption)
- CloudWatch Logs (log group management)
- Lambda (function deployment and execution)
- IAM (role and policy management)
- Account API (contact information access)
- Organizations API (for organization account email)

## Installation

1. **Clone and navigate to the project**:
   ```bash
   cd src/cloudtrail_and_domain_name
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your AWS account information**:
   - Ensure your AWS account has complete contact information at: https://console.aws.amazon.com/billing/home#/account
   - Required fields: Full Name, Address, City, State/Region, Country, Postal Code, Phone Number

4. **Update configuration** (if needed):
   ```bash
   # Edit config.json to match your requirements
   {
     "aws": {
       "account_id": "YOUR_ACCOUNT_ID",
       "region": "us-east-1",
       "bedrock": {
         "budget_tokens": 10000,
         "max_tokens": 64000,
         "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
       }
     },
     "domain_name": "your-domain.com"
   }
   ```

## Deployment

1. **Bootstrap CDK** (first time only):
   ```bash
   npx cdk bootstrap
   ```

2. **Deploy the stack**:
   ```bash
   npx cdk deploy
   ```

3. **Monitor domain registration** (if registering new domain):
   - Domain registration can take several minutes
   - Check AWS console for Route53 Domains operation status
   - Hosted zone creation is automatic after successful registration

## Configuration

### config.json Structure

```json
{
  "aws": {
    "account_id": 123456789012,
    "region": "us-east-1",
    "bedrock": {
      "budget_tokens": 10000,
      "max_tokens": 64000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  },
  "domain_name": "example.com"
}
```

### Domain Registration Behavior

- **Existing domains**: Uses existing hosted zone and exports information
- **New domains**: Registers domain with 1-year duration and auto-renewal enabled
- **Contact information**: Automatically populated from AWS account contact details
- **Privacy protection**: Enabled for all contact types (Admin, Registrant, Tech, Billing)

## Outputs and Exports

The stack creates several outputs for cross-stack references:

- **HostedZoneId**: Route53 hosted zone ID (exported as `{domain-name}-HostedZoneId`)
- **HostedZoneName**: DNS zone name (exported as `{domain-name}-HostedZoneName`) 
- **NameServers**: Comma-separated list of authoritative nameservers
- **DomainName**: The registered domain name
- **RegistrationStatus**: Current domain registration status

## CloudTrail Configuration

### Logging Scope
- **Multi-region**: Captures events from all AWS regions
- **Global services**: Includes IAM, CloudFront, Route53 events
- **Event types**: All management events (read and write operations)

### Storage and Retention
- **S3 storage**: Encrypted with lifecycle rules (Glacier after 90 days, deleted after 5 years)
- **CloudWatch Logs**: 1-year retention for real-time monitoring
- **Access logging**: S3 server access logs stored in separate bucket

## Testing

The project includes comprehensive test suites:

```bash
# Run unit tests
python -m pytest test/test_unit.py -v

# Run integration tests (requires deployed stack)
python -m pytest test/test_integration.py -v

# Run end-to-end DNS tests
python -m pytest test/test_e2e.py -v
```

### Test Coverage
- **Unit tests**: Stack synthesis, resource configuration, Lambda handler logic
- **Integration tests**: Post-deployment verification of AWS resources
- **E2E tests**: DNS resolution and nameserver functionality

## Troubleshooting

### Common Issues

**Domain registration fails**:
- Verify AWS account contact information is complete
- Ensure billing method is configured
- Check domain availability manually in Route53 console

**Missing contact fields error**:
- Configure account contact information: https://console.aws.amazon.com/billing/home#/account
- All fields (name, address, phone, etc.) must be populated

**Hosted zone not found after registration**:
- Domain registration can take up to 15 minutes
- Re-deploy stack after waiting for AWS to create hosted zone
- Check Route53 Domains console for operation status

**CloudTrail permissions errors**:
- Ensure deployment role has CloudTrail, S3, and IAM permissions
- CloudTrail service may need time to propagate bucket policies

### Debug Commands

```bash
# Check stack status
npx cdk diff

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name TenULabsDomainName

# Check domain registration status
aws route53domains get-domain-detail --domain-name your-domain.com --region us-east-1

# List hosted zones
aws route53 list-hosted-zones-by-name --dns-name your-domain.com
```

## Monitoring

### CloudWatch Metrics
- CloudTrail event delivery status
- S3 bucket object counts and sizes
- Lambda function execution metrics and errors

### Alerting
Consider setting up CloudWatch alarms for:
- CloudTrail logging failures
- Unusual API activity patterns
- Domain expiration (via Route53 Domain events)

## Cost Optimization

### Resource Costs
- **Route53 hosted zone**: $0.50/month per zone
- **Domain registration**: Varies by TLD (typically $12-15/year)
- **CloudTrail**: First trail free, data events additional
- **S3 storage**: CloudTrail logs with lifecycle transitions to Glacier
- **CloudWatch Logs**: Pay per GB ingested and stored

### Cost Controls
- S3 lifecycle rules automatically transition logs to cheaper storage
- CloudWatch Logs retention limits storage costs
- Domain auto-renewal prevents costly re-registration

## Security Considerations

### Data Protection
- All S3 buckets encrypted with AWS managed keys
- Public access completely blocked on all buckets
- SSL/TLS required for all S3 operations

### Access Control
- Lambda function uses least-privilege IAM permissions
- CloudTrail logs provide audit trail for all infrastructure changes
- Domain privacy protection masks contact information in WHOIS

### Compliance
- CloudTrail configuration supports compliance frameworks
- Multi-region logging ensures comprehensive audit coverage
- Retention policies align with regulatory requirements

## Development

### Project Structure
```
├── app.py                 # CDK application entry point
├── stack.py              # Main infrastructure stack
├── config.json           # Environment configuration
├── requirements.txt      # Python dependencies
├── cdk.json             # CDK configuration
├── lambda/
│   ├── handler.py       # Domain registration logic
│   └── cfnresponse.py   # CloudFormation response helper
└── test/                # Comprehensive test suite
```

### Adding New Features
1. Update `stack.py` for infrastructure changes
2. Modify `lambda/handler.py` for domain logic changes
3. Update tests to maintain coverage
4. Test changes with `cdk diff` before deployment

## Related Documentation

- [AWS CDK Developer Guide](https://docs.aws.amazon.com/cdk/)
- [Route53 Domains API Reference](https://docs.aws.amazon.com/Route53/latest/APIReference/API_Operations_Amazon_Route_53_Domains.html)
- [CloudTrail User Guide](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/)
- [Route53 Developer Guide](https://docs.aws.amazon.com/route53/latest/developerguide/)
