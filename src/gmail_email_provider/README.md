# Gmail Email Provider CDK Stack

A comprehensive AWS CDK (Cloud Development Kit) stack that configures DNS
records for Gmail email services on a custom domain. This infrastructure-as-code
solution automates the setup of Google site verification and Gmail MX records
in Amazon Route 53.

## Purpose and Key Features

This project streamlines the process of configuring a custom domain to use
Gmail as the email provider by:

- **Automated DNS Configuration**: Creates necessary DNS records in Route 53
- **Google Site Verification**: Sets up TXT records for domain ownership
- **Gmail MX Records**: Configures mail exchange records for Gmail routing
- **Infrastructure as Code**: Manages DNS configuration through version control
- **Multi-Environment Support**: Configurable for different AWS accounts/regions

## Main Components

### Core Infrastructure Components

- **GmailEmailProviderStack**: CDK stack that creates Route 53 DNS records
- **Google Site Verification Record**: TXT record proving domain ownership
- **Gmail MX Record**: Routes email traffic to Google's mail servers
- **Hosted Zone Integration**: Imports existing Route 53 hosted zone

### Configuration Management

- **JSON Configuration**: Centralized settings for AWS and domain parameters
- **Environment-Specific Deployment**: Supports different AWS accounts/regions
- **Configurable TTL**: Adjustable DNS record time-to-live values

## Prerequisites and Requirements

### Python Dependencies

Install the following packages from `requirements.txt`:

```bash
pip install aws-cdk-lib==2.150.0
pip install "constructs>=10.0.0,<11.0.0"
pip install "boto3>=1.34.0"
pip install "boto3-stubs[route53,route53domains,account,organizations]>=1.34.0"
```

### System Dependencies

- **Python 3.7+**: Required for AWS CDK Python bindings
- **Node.js 14+**: Required for AWS CDK CLI and core framework
- **Git**: For version control and repository management

### AWS Requirements

- AWS account with appropriate permissions for Route 53
- Existing Route 53 hosted zone for your domain
- AWS credentials configured (via IAM roles, profiles, or environment variables)

## Configuration Details

### config.json Structure

The configuration file contains the following sections:

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

### Required Configuration Parameters

- **aws.account_id**: Your AWS account ID
- **aws.region**: Target AWS region for deployment
- **domain_name**: The domain to configure for Gmail
- **google_site_verification**: Google verification token
- **ttl**: DNS record TTL in seconds (optional, defaults to 300)

### CDK Configuration

The `cdk.json` file configures CDK behavior:

- **app**: Entry point (`python3 app.py`)
- **watch**: File watching patterns for development
- **context**: Feature flags and CDK-specific settings

## Usage Instructions

### Installation Steps

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd gmail-email-provider-cdk
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI** (if not already installed):

   ```bash
   npm install -g aws-cdk
   ```

### Configuration Setup

1. **Update config.json** with your specific values:

   ```bash
   cp config.json.example config.json
   # Edit config.json with your AWS account ID, domain, and verification token
   ```

2. **Configure AWS credentials** using one of these methods:

   - AWS IAM roles (recommended for EC2/Lambda)
   - AWS profiles: `aws configure --profile myprofile`
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Deployment Commands

1. **Bootstrap CDK** (first-time setup per account/region):

   ```bash
   cdk bootstrap
   ```

2. **Synthesize CloudFormation template**:

   ```bash
   cdk synth
   ```

3. **Deploy the stack**:

   ```bash
   cdk deploy
   ```

4. **View stack outputs**:

   ```bash
   cdk deploy --outputs-file outputs.json
   ```

### Using the Deployed Resources

After successful deployment:

1. **Verify DNS records** in Route 53 console
2. **Complete Google Workspace setup** using the verification record
3. **Test email routing** by sending test emails to your domain
4. **Monitor DNS propagation** (may take up to 48 hours globally)

## Architecture Overview

### Component Interaction Flow

```text
app.py → stack.py → Route 53 → Gmail Services
   ↓         ↓           ↓
config.json  CDK     DNS Records
```

### DNS Record Creation Process

1. **Stack Initialization**: Loads configuration and imports existing hosted zone
2. **Google Verification**: Creates TXT record for domain ownership proof
3. **MX Record Setup**: Configures mail routing to Gmail servers
4. **Output Generation**: Provides verification details and record information

### Integration Points

- **Route 53 Integration**: Imports existing hosted zone via CloudFormation exports
- **Google Workspace**: Verification record enables Gmail service activation
- **Email Routing**: MX records direct email traffic to Google's infrastructure

### Data Flow

1. **Configuration Input**: JSON files provide deployment parameters
2. **CDK Synthesis**: Converts Python code to CloudFormation templates
3. **AWS Deployment**: Creates Route 53 records in specified hosted zone
4. **DNS Resolution**: Public DNS queries resolve to Gmail servers

## Security Considerations

### Access Control

- **IAM Permissions**: Limit Route 53 access to necessary actions only
- **Hosted Zone Security**: Ensure proper delegation and zone management
- **Configuration Protection**: Store sensitive tokens securely

### DNS Security

- **DNSSEC**: Consider enabling for enhanced DNS security
- **Record Monitoring**: Implement alerts for unauthorized DNS changes
- **TTL Configuration**: Balance performance with security update speed

### Best Practices

- Use IAM roles instead of access keys when possible
- Regularly rotate Google verification tokens
- Monitor DNS record changes through CloudTrail
- Implement least-privilege access policies

## Troubleshooting Tips

### Common Deployment Issues

**CDK Bootstrap Errors**:

```bash
# Ensure proper AWS credentials and permissions
aws sts get-caller-identity
cdk bootstrap --profile your-profile
```

**Import Value Not Found**:

- Verify the hosted zone exists and exports the required values
- Check export naming convention: `{domain-with-dashes}-HostedZoneId`

**Permission Denied Errors**:

- Ensure IAM user/role has Route53 and CloudFormation permissions
- Verify account ID matches the configuration

### DNS Propagation Issues

**Verification Not Working**:

1. Check DNS record creation in Route 53 console
2. Use DNS lookup tools: `nslookup -type=TXT yourdomain.com`
3. Wait for DNS propagation (up to 48 hours)

**Email Not Routing**:

1. Verify MX record points to `smtp.google.com` with priority 1
2. Check Google Workspace configuration
3. Test with external email providers

### Development Workflow Issues

**CDK Watch Mode**:

```bash
# Use watch mode for iterative development
cdk watch
```

**Stack Diff Checking**:

```bash
# Review changes before deployment
cdk diff
```
