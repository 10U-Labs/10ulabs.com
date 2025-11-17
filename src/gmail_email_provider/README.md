# Gmail Email Provider Infrastructure

A comprehensive AWS CDK infrastructure project that configures DNS records for
Gmail email services on the 10ulabs.com domain. This stack creates the
necessary Route 53 records to enable Gmail as the email provider, including
Google site verification and MX records for email routing.

## Purpose and Key Features

This infrastructure automates the DNS configuration required to use Gmail as
an email provider for a custom domain. It provides:

- **Google Site Verification**: Automatically creates TXT records for Google
  domain verification
- **Gmail MX Records**: Configures mail exchange records pointing to Google's
  SMTP servers
- **Imported Zone Management**: References existing Route 53 hosted zones
  through CloudFormation imports
- **Configurable TTL**: Allows customization of DNS record time-to-live values
- **Tagged Resources**: Applies consistent tags for resource management

## Resources Created

This CDK stack creates the following AWS resources:

### Route 53 Records

- **TXT Record**: Google site verification record with the format
  `google-site-verification={verification-code}`
- **MX Record**: Mail exchange record pointing to `smtp.google.com` with
  priority 1

### CloudFormation Outputs

- **GoogleVerificationRecord**: Domain name of the verification TXT record
- **GoogleVerificationValue**: The verification string value
- **GmailMxRecordOutput**: Domain name of the Gmail MX record

## Prerequisites and Requirements

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```txt
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[route53,route53domains,account,organizations]>=1.34.0
```

### System Dependencies

- **Python 3.8+**: Required for AWS CDK Python applications
- **Node.js 14.15.0+**: Required for AWS CDK toolkit
- **Git**: For version control and repository management

### AWS Prerequisites

- **AWS Account**: Valid AWS account with appropriate permissions
- **Route 53 Hosted Zone**: Pre-existing hosted zone for your domain with
  exported CloudFormation values
- **AWS Credentials**: Configured AWS credentials with Route 53 permissions

## Configuration Details

### config.json

The main configuration file contains:

```json
{
  "aws": {
    "account_id": 781581267945,
    "bedrock": {
      "max_tokens_reasoning": 4000,
      "max_tokens_generation": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "region": "us-east-1"
  },
  "domain_name": "10ulabs.com",
  "google_site_verification": "vkFVA-Ru1PwnePtOWeOt0k5bmzOpHtjfDZU-PfUKjRM",
  "ttl": 300
}
```

**Configuration Parameters:**

- `aws.account_id`: Target AWS account ID for deployment
- `aws.region`: AWS region for resource deployment
- `domain_name`: The domain name to configure for Gmail
- `google_site_verification`: Google verification code for domain ownership
- `ttl`: DNS record time-to-live in seconds (default: 300)

### cdk.json

CDK-specific configuration with feature flags and watch settings:

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
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true
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

### Configuration Setup

1. **Update config.json** with your specific values:
   - Replace `account_id` with your AWS account ID
   - Update `domain_name` with your domain
   - Set your `google_site_verification` code
   - Adjust `ttl` if needed

2. **Ensure hosted zone exports exist** with the naming convention:
   - `{domain-name-with-dashes}-HostedZoneId`
   - `{domain-name-with-dashes}-HostedZoneName`

### Deployment

1. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap
   ```

2. **Synthesize the stack**:

   ```bash
   cdk synth
   ```

3. **Deploy the infrastructure**:

   ```bash
   cdk deploy
   ```

4. **Verify deployment**:

   ```bash
   cdk ls
   ```

### Using the Deployed Resources

After deployment, the DNS records will be automatically configured. You can:

1. **Verify Google ownership** through Google Search Console
2. **Configure Gmail** for your custom domain through Google Workspace
3. **Test email routing** by sending emails to addresses at your domain

## Architecture Overview

### Component Interactions

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK Stack     │───▶│   Route 53       │───▶│  Google Mail    │
│   (Python)      │    │   DNS Records    │    │   Services      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │
        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│  CloudFormation │    │   Domain Email   │
│    Outputs      │    │   Verification   │
└─────────────────┘    └──────────────────┘
```

### Data Flow

1. **CDK Synthesis**: Python code generates CloudFormation templates
2. **DNS Configuration**: Route 53 records are created/updated
3. **Google Verification**: TXT record enables domain ownership verification
4. **Email Routing**: MX record directs email traffic to Gmail servers

### Import Dependencies

The stack relies on CloudFormation cross-stack references:

- Imports existing hosted zone ID and name
- Uses `Fn.import_value()` to reference exported values
- Maintains loose coupling between infrastructure components

## Security Considerations

### Access Control

- **IAM Permissions**: Ensure deployment role has Route 53 record management
  permissions
- **Cross-Stack References**: Verify imported hosted zone values are from
  trusted sources
- **Configuration Management**: Protect sensitive configuration values

### DNS Security

- **TTL Configuration**: Balance between propagation speed and DNS caching
- **Record Validation**: Verify MX and TXT records point to legitimate Google
  services
- **Domain Verification**: Ensure Google verification codes are kept secure

### Best Practices

- **Least Privilege**: Use minimal required AWS permissions
- **Configuration Validation**: Validate all configuration parameters before
  deployment
- **Monitoring**: Set up DNS query monitoring and alerting

## Troubleshooting

### Common Issues

**Import Value Not Found:**

```bash
# Check if the source stack exports exist
aws cloudformation list-exports --query 'Exports[?Name==`10ulabs-com-HostedZoneId`]'
```

**DNS Propagation Issues:**

```bash
# Test DNS record creation
dig TXT 10ulabs.com
dig MX 10ulabs.com
```

**Configuration Errors:**

- Verify `config.json` syntax and required fields
- Ensure Google verification code format is correct
- Check domain name format and spelling

### Debug Commands

**View synthesized template:**

```bash
cdk synth --verbose
```

**Check stack differences:**

```bash
cdk diff
```

**View stack outputs:**

```bash
aws cloudformation describe-stacks --stack-name GmailEmailProvider
```

### Recovery Procedures

**Stack Update Failures:**

1. Check CloudFormation console for detailed error messages
2. Verify IAM permissions for Route 53 operations
3. Ensure hosted zone imports are still available

**DNS Record Conflicts:**

1. Check for existing conflicting records
2. Use `cdk destroy` and redeploy if necessary
3. Manually clean up orphaned DNS records if needed
