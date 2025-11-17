# 10ULabs Domain Infrastructure

AWS CDK infrastructure for managing the `10ulabs.com` domain, including
automated domain registration, Route53 hosted zone management, and
comprehensive CloudTrail logging.

## Overview

This infrastructure automatically registers and manages a domain name
through AWS Route53 Domains, creates the necessary hosted zone for DNS
management, and sets up comprehensive CloudTrail logging for security
and compliance. The solution uses AWS Lambda custom resources to handle
domain registration workflows and automatically configures DNS nameservers.

## Key Features

- **Automated Domain Registration**: Registers domains if not already owned
- **Route53 Integration**: Creates and manages hosted zones automatically  
- **Contact Information**: Uses AWS account contact details for registration
- **Security Logging**: Comprehensive CloudTrail logging with S3 storage
- **Cost Optimization**: Lifecycle policies for long-term log retention
- **Error Handling**: Robust retry logic and status monitoring

## AWS Resources Created

### Core Domain Resources

- **Lambda Function**: Custom resource handler for domain registration
- **Route53 Hosted Zone**: DNS management for the domain
- **Custom Resource**: Orchestrates domain registration workflow

### Security and Compliance

- **CloudTrail**: Multi-region trail capturing all API activity
- **S3 Bucket (CloudTrail)**: Stores CloudTrail logs with lifecycle policies
- **S3 Bucket (Access Logs)**: Stores S3 access logs for audit trails
- **CloudWatch Log Group**: Real-time CloudTrail log streaming

### IAM Permissions

- **Lambda Execution Role**: Permissions for Route53, Account, and
  Organizations APIs
- **CloudTrail Service Role**: Permissions for S3 and CloudWatch Logs

## Prerequisites

### System Dependencies

- **Node.js** (v18 or later) - Required for AWS CDK
- **Python** (3.11 or later) - Required for CDK app and Lambda functions
- **Git** - For cloning and version control

### Python Dependencies

```bash
pip install -r requirements.txt
```

The following packages are required (from `requirements.txt`):

- `aws-cdk-lib==2.150.0` - AWS CDK core library
- `constructs>=10.0.0,<11.0.0` - CDK constructs framework  
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` -
  Type hints for boto3

### AWS Account Requirements

- **Account Contact Information**: Complete billing address, phone, and
  contact details must be configured in AWS Account settings
- **Organizations Access** (optional): If account is in AWS Organizations,
  the email will be automatically detected
- **Route53 Domains Permissions**: Ability to register domains and manage
  hosted zones
- **Account API Access**: Permissions to read account contact information

## Configuration

### config.json

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
  "domain_name": "10ulabs.com"
}
```

### CDK Configuration (cdk.json)

The CDK configuration enables:

- **Hot Reloading**: File watching for development
- **Security Features**: Secret usage validation and IMDS v2
- **Modern Defaults**: Latest CDK feature flags enabled

## Installation and Deployment

### 1. Clone and Setup

```bash
git clone <repository-url>
cd 10ulabs.com
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install CDK globally (if not already installed)
npm install -g aws-cdk
```

### 3. Configure AWS Credentials

```bash
# Configure AWS credentials (choose one method)
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### 4. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://781581267945/us-east-1
```

### 5. Deploy Infrastructure

```bash
# Preview changes
cdk diff

# Deploy the stack
cdk deploy TenULabsDomainName
```

## Usage

### Domain Registration Workflow

1. **Existing Domain**: If domain is already registered, the system detects
   the existing hosted zone and uses it
2. **New Domain**: If domain is available, it will be registered
   automatically using AWS account contact information
3. **Hosted Zone**: A Route53 hosted zone is created or identified for
   DNS management

### DNS Management

After deployment, use the hosted zone for DNS records:

```python
# Example: Adding DNS records in other CDK stacks
from aws_cdk import aws_route53 as route53

# Import the hosted zone
hosted_zone = route53.HostedZone.from_lookup(
    self, "ImportedZone",
    domain_name="10ulabs.com"
)

# Add records
route53.ARecord(
    self, "WebsiteRecord",
    zone=hosted_zone,
    target=route53.RecordTarget.from_ip_addresses("1.2.3.4")
)
```

### Stack Outputs

The deployment provides these outputs:

- **DomainName**: The registered domain name
- **HostedZoneId**: Route53 hosted zone ID (exported for cross-stack usage)
- **HostedZoneName**: Route53 hosted zone name (exported)
- **NameServers**: Comma-separated list of authoritative nameservers
- **RegistrationStatus**: Current domain registration status

## Architecture

### Component Interaction Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK Deploy    │───▶│  Lambda Handler  │───▶│  Route53        │
└─────────────────┘    └──────────────────┘    │  Domains API    │
                                ▼              └─────────────────┘
                       ┌──────────────────┐              ▼
                       │  Account API     │    ┌─────────────────┐
                       │  (Contact Info)  │    │  Hosted Zone    │
                       └──────────────────┘    │  Creation       │
                                              └─────────────────┘
```

### Authentication and Authorization

- **Lambda Function**: Uses IAM role with minimal required permissions
- **Account API**: Accesses billing contact information for domain
  registration
- **Organizations API**: Attempts to retrieve organization root email
  (gracefully handles accounts not in organizations)
- **Route53 APIs**: Manages hosted zones and domain registration

### Data Flow

1. **Contact Information**: Retrieved from AWS Account/Organizations APIs
2. **Domain Check**: Verifies if domain exists or is available for
   registration
3. **Registration**: If needed, registers domain with AWS contact details
4. **Zone Detection**: Locates or waits for hosted zone creation
5. **Output Generation**: Provides hosted zone details for other stacks

## Security Considerations

### Data Protection

- **Contact Information**: Automatically enables privacy protection for
  all domain contacts
- **S3 Encryption**: All S3 buckets use server-side encryption
- **SSL Enforcement**: All S3 buckets require HTTPS access
- **Access Logging**: S3 access logs capture all bucket interactions

### Audit and Compliance

- **CloudTrail**: Captures all API calls across all regions
- **Log Retention**: CloudWatch logs retained for 1 year
- **Long-term Storage**: S3 logs transitioned to Glacier after 90 days
- **Log Integrity**: CloudTrail provides log file integrity validation

### IAM Security

- **Principle of Least Privilege**: Lambda function has minimal required
  permissions
- **Resource-Specific**: IAM policies target specific AWS services only
- **No Persistent Resources**: Domain registration is event-driven only

## Troubleshooting

### Common Issues

#### Domain Registration Timeout

```
Error: Hosted zone not created within timeout period
```

**Solution**: Domain registration can take several minutes. Wait 5-10
minutes and re-deploy:

```bash
cdk deploy TenULabsDomainName --force
```

#### Missing Contact Information

```
Error: AWS account missing contact fields
```

**Solution**: Configure complete contact information at:
<https://console.aws.amazon.com/billing/home#/account>

Required fields: Full Name, Address, City, State, Country, Postal Code,
Phone Number

#### Phone Number Format Issues

```
Error: Invalid phone number format
```

**Solution**: Ensure phone number in AWS account settings includes country
code or is in international format. The Lambda function automatically
formats phone numbers using country dialing codes.

### Debugging Steps

1. **Check CloudWatch Logs**: Lambda function logs provide detailed
   registration status

   ```bash
   aws logs describe-log-groups --log-group-name-prefix \
     "/aws/lambda/TenULabsDomainName"
   ```

2. **Verify Account Settings**: Ensure AWS account has complete contact
   information

3. **Check Domain Status**: Monitor domain registration operation:

   ```bash
   aws route53domains get-operation-detail --operation-id <operation-id>
   ```

4. **Force Re-deployment**: If resources are in inconsistent state:

   ```bash
   cdk destroy TenULabsDomainName
   cdk deploy TenULabsDomainName
   ```

### Monitoring

- **CloudWatch Metrics**: Monitor Lambda function execution and errors
- **CloudTrail**: Review all API calls for security and debugging
- **Route53 Health Checks**: Set up health checks for critical DNS records
- **Cost Monitoring**: Track domain registration and DNS query costs
