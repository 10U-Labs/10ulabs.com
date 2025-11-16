# Gmail Email Provider DNS Configuration

A CDK-based infrastructure project that configures DNS records for Gmail
email services on the 10ulabs.com domain. This stack creates the necessary
DNS records to enable Gmail as the email provider, including MX records for
mail routing and Google site verification records for domain ownership.

## Purpose and Key Features

- **Gmail Integration**: Configures DNS records to use Gmail/Google
  Workspace for email services
- **Domain Verification**: Sets up Google site verification TXT records
  for domain ownership confirmation
- **Automated DNS Management**: Uses AWS Route 53 for DNS record management
- **Infrastructure as Code**: Fully declarative infrastructure using AWS CDK
- **Cross-Stack Integration**: Imports existing hosted zone from another
  stack for centralized DNS management

## Resources Created

This infrastructure creates the following AWS resources:

- **Route 53 TXT Record**: Google site verification record to prove domain
  ownership to Google services
- **Route 53 MX Record**: Mail exchange record pointing to
  `smtp.google.com` with priority 1 for Gmail email routing

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

- **Python 3.7+**: Required for AWS CDK Python bindings
- **Node.js 14+**: Required for AWS CDK CLI and core functionality
- **AWS CDK CLI**: Install globally with `npm install -g aws-cdk`

### AWS Requirements

- AWS account with appropriate permissions for Route 53
- Existing Route 53 hosted zone for the target domain
- The hosted zone must export its ID and name for cross-stack references

### Domain Prerequisites

- Domain must be configured in Google Workspace or Gmail
- Google site verification code must be obtained from Google Search Console

## Configuration

### config.json

The main configuration file contains:

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

- `aws.account_id`: Target AWS account ID
- `aws.region`: AWS region for deployment
- `domain_name`: Domain name for DNS record configuration
- `google_site_verification`: Google verification code from Google Search
  Console
- `ttl`: DNS record time-to-live in seconds (default: 300)

### CDK Configuration

The `cdk.json` file configures CDK behavior:

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__"]
  }
}
```

## Usage Instructions

### Installation

1. Clone the repository and navigate to the project directory

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK CLI (if not already installed):

   ```bash
   npm install -g aws-cdk
   ```

### Configuration Setup

1. Update `config.json` with your specific values:
   - Set your AWS account ID and preferred region
   - Configure your domain name
   - Add your Google site verification code

2. Ensure your AWS credentials are configured:

   ```bash
   aws configure
   ```

### Deployment

1. Bootstrap CDK in your AWS account (first time only):

   ```bash
   cdk bootstrap
   ```

2. Synthesize the CloudFormation template:

   ```bash
   cdk synth
   ```

3. Deploy the infrastructure:

   ```bash
   cdk deploy GmailEmailProvider
   ```

4. Confirm deployment when prompted

### Verification

After deployment, verify the DNS records:

```bash
dig TXT 10ulabs.com
dig MX 10ulabs.com
```

### Cleanup

To remove all resources:

```bash
cdk destroy GmailEmailProvider
```

## Architecture Overview

### Component Interaction

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gmail/Google  │    │   Route 53      │    │  Existing       │
│   Workspace     │◄───┤   DNS Records   │◄───┤  Hosted Zone    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Email Flow    │
                       │   Domain Verify │
                       └─────────────────┘
```

### DNS Record Flow

1. **Hosted Zone Import**: The stack imports an existing Route 53 hosted
   zone using CloudFormation cross-stack references
2. **TXT Record Creation**: Creates Google site verification record for
   domain ownership proof
3. **MX Record Creation**: Creates mail exchange record pointing to Gmail
   servers
4. **Email Routing**: Gmail servers receive email for the domain based on
   MX record configuration

### Cross-Stack Integration

The stack expects these CloudFormation exports from the hosted zone stack:

- `{domain-name}-HostedZoneId`: The Route 53 hosted zone ID
- `{domain-name}-HostedZoneName`: The hosted zone name

Example exports for `10ulabs.com`:

- `10ulabs-com-HostedZoneId`
- `10ulabs-com-HostedZoneName`

## Security Considerations

### DNS Security

- **TTL Configuration**: Low TTL (300 seconds) allows for quick DNS
  propagation but may increase query load
- **Record Validation**: Google site verification provides domain ownership
  proof
- **MX Priority**: Single MX record with priority 1 ensures all mail routes
  through Gmail

### Access Control

- **IAM Permissions**: Deployment requires Route 53 full access permissions
- **Cross-Stack References**: Relies on exported values from trusted
  hosted zone stack
- **Regional Deployment**: Deployed in us-east-1 for optimal Route 53
  performance

### Best Practices

- Store sensitive verification codes securely
- Monitor DNS record changes through CloudTrail
- Use least-privilege IAM policies for deployment
- Validate DNS propagation after deployment

## Troubleshooting

### Common Issues

**DNS Records Not Propagating**

- Check TTL settings in configuration
- Verify DNS propagation with multiple DNS checkers
- Ensure hosted zone is correctly configured

**Stack Deployment Failures**

- Verify AWS credentials and permissions
- Check that referenced hosted zone exports exist
- Confirm account ID and region in configuration

**Google Verification Issues**

- Ensure verification code is correct and current
- Check that TXT record is properly formatted
- Verify domain ownership in Google Search Console

### Debugging Commands

Check CloudFormation stack status:

```bash
aws cloudformation describe-stacks --stack-name GmailEmailProvider
```

Verify exported values from hosted zone stack:

```bash
aws cloudformation list-exports
```

Test DNS resolution:

```bash
nslookup -type=MX 10ulabs.com
nslookup -type=TXT 10ulabs.com
```

### Validation Steps

1. **Pre-deployment**: Verify hosted zone exports exist
2. **Post-deployment**: Check DNS record creation in Route 53 console
3. **Email testing**: Send test email to verify mail routing
4. **Google verification**: Confirm domain verification in Google Search
   Console
