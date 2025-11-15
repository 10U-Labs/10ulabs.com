# Gmail Email Provider Infrastructure

This AWS CDK project configures DNS records to enable Gmail as the email
provider for a domain. It creates the necessary Route53 DNS records including
Google site verification and Gmail MX records to route email through Google's
servers.

## Purpose and Key Features

- **Gmail Integration**: Configures DNS records to use Gmail as email provider
- **Google Verification**: Sets up Google site verification for domain ownership
- **Route53 Management**: Manages DNS records through AWS Route53
- **Infrastructure as Code**: Uses AWS CDK for reproducible deployments
- **Cross-Stack Integration**: Imports existing hosted zone from another stack

## Resources Created

This infrastructure creates the following AWS resources:

- **Route53 TXT Record**: Google site verification record for domain ownership
- **Route53 MX Record**: Mail exchange record pointing to Gmail servers
  (`smtp.google.com` with priority 1)
- **CloudFormation Outputs**: Domain names and verification values for reference

## Prerequisites and Requirements

### System Dependencies

- **Node.js** (v18 or later) - Required for AWS CDK
- **Python** (3.8 or later) - Runtime for the CDK application
- **Git** - For version control and repository management

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0` - AWS CDK core library
- `constructs>=10.0.0,<11.0.0` - CDK constructs framework
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` - Type
  stubs for boto3

### AWS Prerequisites

- **AWS Account**: Valid AWS account with appropriate permissions
- **Existing Hosted Zone**: A Route53 hosted zone must exist and export:
  - `{domain-name}-HostedZoneId`
  - `{domain-name}-HostedZoneName`
- **AWS Credentials**: Configured via environment variables, AWS credentials
  file, or IAM roles
- **Route53 Permissions**: IAM permissions for Route53 record management

## Configuration

Create a `config.json` file with the following structure:

```json
{
  "domain_name": "example.com",
  "google_site_verification": "your-google-verification-code",
  "ttl": 300,
  "aws": {
    "account_id": "123456789012",
    "region": "us-east-1"
  }
}
```

### Configuration Parameters

| Parameter | Required | Description | Default |
| --- | --- | --- | --- |
| `domain_name` | Yes | The domain to configure Gmail for | N/A |
| `google_site_verification` | Yes | Google site verification code | N/A |
| `ttl` | No | DNS record TTL in seconds | 300 |
| `aws.account_id` | Yes | AWS account ID | N/A |
| `aws.region` | Yes | AWS region for deployment | N/A |

## Usage Instructions

### Installation

1. Clone the repository and navigate to the project directory:

   ```bash
   git clone <repository-url>
   cd gmail-email-provider
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK globally:

   ```bash
   npm install -g aws-cdk
   ```

### Configuration Setup

1. Create your configuration file:

   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` with your domain and Google verification details

3. Obtain the Google site verification code from Google Search Console

### Deployment

1. Bootstrap CDK (first time only):

   ```bash
   cdk bootstrap
   ```

2. Review the deployment plan:

   ```bash
   cdk diff
   ```

3. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

4. Confirm the deployment when prompted

### Verification

After deployment, verify the DNS records:

1. Check MX record:

   ```bash
   nslookup -type=MX your-domain.com
   ```

2. Check TXT record:

   ```bash
   nslookup -type=TXT your-domain.com
   ```

3. Verify in Google Search Console that domain ownership is confirmed

## Architecture Overview

### Component Interaction

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK App       │───▶│  Route53 Records │───▶│  Gmail Servers  │
│   (app.py)      │    │  - MX Record     │    │  smtp.google.com│
└─────────────────┘    │  - TXT Record    │    └─────────────────┘
         │              └──────────────────┘
         ▼
┌─────────────────┐    ┌──────────────────┐
│ Gmail Stack     │───▶│ Existing Hosted  │
│ (stack.py)      │    │ Zone (Imported)  │
└─────────────────┘    └──────────────────┘
```

### DNS Resolution Flow

1. **Email Delivery**: Email providers lookup MX records for the domain
2. **Route53 Response**: Returns `smtp.google.com` with priority 1
3. **Gmail Processing**: Google's servers receive and process the email
4. **Domain Verification**: Google uses TXT record to verify domain ownership

### Cross-Stack Dependencies

- **Hosted Zone Import**: Uses CloudFormation exports from existing DNS stack
- **Export Format**: `{domain-with-dashes}-HostedZoneId` and
  `{domain-with-dashes}-HostedZoneName`
- **Stack Coupling**: Requires the DNS foundation stack to be deployed first

## Security Considerations

### Access Control

- **IAM Permissions**: Limit Route53 permissions to necessary records only
- **Cross-Account Access**: Ensure proper cross-account roles if applicable
- **Principle of Least Privilege**: Grant minimum required permissions

### DNS Security

- **TTL Settings**: Use appropriate TTL values (300 seconds default)
- **Record Validation**: Verify MX and TXT records after deployment
- **Domain Verification**: Complete Google domain verification process

### Sensitive Information

- **Configuration Security**: Protect `config.json` containing verification codes
- **Environment Variables**: Consider using AWS Secrets Manager for sensitive data
- **Version Control**: Exclude sensitive configuration from Git commits

## Troubleshooting

### Common Issues

**Stack Import Errors**:

```text
Error: No export named {domain-name}-HostedZoneId found
```

- Verify the DNS foundation stack is deployed
- Check export names match the expected format
- Ensure domain name in config matches the exported zone

**Google Verification Failures**:

- Confirm TXT record is properly created and propagated
- Check DNS propagation with online tools
- Verify verification code matches Google Search Console

**MX Record Issues**:

```bash
# Test MX record resolution
dig MX your-domain.com

# Expected output should include:
# your-domain.com. 300 IN MX 1 smtp.google.com.
```

**Permission Errors**:

- Verify AWS credentials are configured correctly
- Ensure IAM user/role has Route53 permissions
- Check account ID and region in configuration

### Debugging Steps

1. **Verify Configuration**:

   ```bash
   python3 -c "import json; print(json.load(open('config.json')))"
   ```

2. **Check Stack Status**:

   ```bash
   cdk list
   cdk diff
   ```

3. **Validate DNS Propagation**:

   ```bash
   # Check from multiple DNS servers
   nslookup -type=MX your-domain.com 8.8.8.8
   nslookup -type=TXT your-domain.com 1.1.1.1
   ```

4. **CloudFormation Console**: Review stack events and outputs in AWS Console
