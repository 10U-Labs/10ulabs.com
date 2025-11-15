# Gmail Email Provider Infrastructure

This AWS CDK infrastructure project configures DNS records for using Gmail as
the email provider for a domain. It sets up the necessary MX records and Google
site verification to enable Gmail email services for the specified domain.

## Overview

This infrastructure automatically creates and manages DNS records required to
configure Gmail as the email provider for your domain. The stack deploys Route
53 DNS records including MX records for Gmail email routing and Google site
verification TXT records for domain ownership verification.

## Key Features

- **Gmail MX Record Configuration**: Automatically configures MX records to
  route email through Gmail's SMTP servers
- **Google Site Verification**: Sets up TXT records for Google domain
  ownership verification
- **Configurable TTL**: Allows customization of DNS record time-to-live values
- **Cross-Stack Integration**: Imports existing hosted zone from another stack
- **AWS CDK Best Practices**: Uses Infrastructure as Code with proper tagging
  and outputs

## AWS Resources Created

This stack creates the following AWS resources:

- **Route53 TXT Record**: Google site verification record for domain ownership
- **Route53 MX Record**: Gmail mail exchange record pointing to
  `smtp.google.com` with priority 1
- **CloudFormation Outputs**: Provides record names and values for reference

## Prerequisites

### System Dependencies

- **Python 3.8 or higher**: Required for AWS CDK Python support
- **Node.js 18 or higher**: Required for AWS CDK CLI
- **Git**: For version control and repository management

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

The project requires these specific packages:

- `aws-cdk-lib==2.150.0`: AWS CDK core library
- `constructs>=10.0.0,<11.0.0`: CDK constructs framework
- `boto3>=1.34.0`: AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`: Type
  stubs for development

### AWS Configuration

- **AWS Account**: Valid AWS account with appropriate permissions
- **AWS Credentials**: Configured via IAM user, role, or AWS SSO
- **Route53 Permissions**: Ability to create and manage DNS records
- **Existing Hosted Zone**: A Route53 hosted zone must already exist and
  export its ID and name

### Pre-existing Infrastructure

This stack requires an existing Route53 hosted zone that exports the following
CloudFormation values:

- `{domain-name}-HostedZoneId`: The hosted zone ID
- `{domain-name}-HostedZoneName`: The hosted zone name

Where `{domain-name}` has dots replaced with hyphens (e.g.,
`10ulabs-com-HostedZoneId`).

## Configuration

### config.json

The main configuration file defines deployment parameters:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1"
  },
  "domain_name": "10ulabs.com",
  "google_site_verification": "vkFVA-Ru1PwnePtOWeOt0k5bmzOpHtjfDZU-PfUKjRM",
  "ttl": 300
}
```

#### Configuration Parameters

- **aws.account_id**: Target AWS account ID for deployment
- **aws.region**: AWS region for resource deployment
- **domain_name**: Domain name to configure Gmail for
- **google_site_verification**: Google site verification token
- **ttl**: DNS record time-to-live in seconds (default: 300)

### cdk.json

CDK configuration file with deployment settings:

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

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd gmail-email-provider
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI** (if not already installed):

   ```bash
   npm install -g aws-cdk
   ```

### Configuration Setup

1. **Update config.json** with your domain details:

   ```bash
   cp config.json.example config.json
   # Edit config.json with your values
   ```

2. **Obtain Google site verification token**:
   - Visit Google Search Console
   - Add your domain property
   - Choose "HTML tag" verification method
   - Copy the verification token from the meta tag

### Deployment

1. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap
   ```

2. **Deploy the stack**:

   ```bash
   cdk deploy
   ```

3. **Review changes** before deployment:

   ```bash
   cdk diff
   ```

### Verification

After deployment, verify the DNS records are created:

1. **Check MX record**:

   ```bash
   nslookup -type=MX yourdomain.com
   ```

2. **Check TXT record**:

   ```bash
   nslookup -type=TXT yourdomain.com
   ```

3. **Verify in Google Search Console**:
   - Return to Google Search Console
   - Click "Verify" for your domain property

## Architecture Overview

### Component Interaction

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK Stack     │────│   Route53 Zone   │────│  Gmail SMTP     │
│                 │    │                  │    │                 │
│ - MX Record     │    │ - DNS Records    │    │ - Email Routing │
│ - TXT Record    │    │ - Domain Config  │    │ - Mail Delivery │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Configuration Loading**: App reads config.json for deployment parameters
2. **Stack Initialization**: CDK creates stack with imported hosted zone
3. **Record Creation**: DNS records are created in Route53
4. **Email Routing**: Gmail SMTP servers handle email for the domain
5. **Verification**: Google verifies domain ownership via TXT record

### Integration Points

- **Cross-Stack References**: Imports hosted zone from existing infrastructure
- **CloudFormation Outputs**: Provides record details for other stacks
- **Tag Inheritance**: Applies project-wide tags to all resources

## Security Considerations

### DNS Security

- **Record Validation**: Ensures proper MX record configuration
- **TTL Management**: Configurable TTL values for cache control
- **Zone Protection**: Uses existing hosted zone with proper access controls

### Access Control

- **IAM Permissions**: Requires Route53 DNS management permissions
- **Account Isolation**: Deploys to specific AWS account only
- **Resource Tagging**: Enables cost allocation and access tracking

### Best Practices

- **Configuration Management**: Sensitive values should be stored securely
- **Version Control**: Track infrastructure changes through Git
- **Least Privilege**: Grant minimum required AWS permissions

## Troubleshooting

### Common Issues

#### Deployment Failures

**Error**: `HostedZoneId not found in exports`

```text
Solution: Ensure the source hosted zone stack exports the required values:
- {domain-name}-HostedZoneId
- {domain-name}-HostedZoneName
```

**Error**: `Invalid google_site_verification token`

```text
Solution: Verify the token is correct from Google Search Console:
1. Go to Search Console property settings
2. Copy the exact verification token
3. Update config.json with the new token
```

#### DNS Propagation

**Issue**: DNS records not resolving immediately

```bash
# Check DNS propagation
dig MX yourdomain.com @8.8.8.8
dig TXT yourdomain.com @8.8.8.8

# Wait for TTL expiration (default 300 seconds)
```

#### Permission Issues

**Error**: `Access Denied` during deployment

```text
Required IAM permissions:
- route53:ChangeResourceRecordSets
- route53:GetHostedZone
- route53:ListResourceRecordSets
- cloudformation:CreateStack
- cloudformation:UpdateStack
```

### Debug Commands

```bash
# View stack resources
cdk list

# Show generated CloudFormation
cdk synth

# Compare deployed vs local changes
cdk diff

# View deployment logs
cdk deploy --verbose
```

### Support Resources

- AWS CDK Documentation: <https://docs.aws.amazon.com/cdk/>
- Route53 DNS Records: <https://docs.aws.amazon.com/route53/latest/developerguide/>
- Google Search Console: <https://search.google.com/search-console/>
