# 10ULabs Domain Infrastructure

AWS CDK infrastructure for automated domain registration and comprehensive CloudTrail logging for the `10ulabs.com` domain.

## Overview

This project provides a complete AWS infrastructure solution that:

- **Automatically registers domains** using Route53 Domains with privacy protection
- **Sets up comprehensive CloudTrail logging** with S3 storage and CloudWatch Logs integration  
- **Creates Route53 hosted zones** with proper DNS delegation
- **Implements security best practices** including encryption, access logging, and public access blocking
- **Provides cost optimization** through lifecycle policies and appropriate retention settings

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Lambda        │    │   Route53        │    │   CloudTrail    │
│   Function      │───▶│   Hosted Zone    │    │   Trail         │
│                 │    │                  │    │                 │
│ Domain          │    │ DNS Management   │    │ Multi-region    │
│ Registration    │    │ Name Servers     │    │ Logging         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │   S3 Buckets    │
         │                       │              │                 │
         │                       │              │ • CloudTrail    │
         │                       │              │ • Access Logs   │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │ CloudWatch Logs │
         │                       │              │                 │
         │                       │              │ 1-year retention│
         │                       │              └─────────────────┘
         ▼                       │
┌─────────────────┐              │
│ AWS Account     │              │
│ Contact Info    │              │
│                 │              │
│ • Organizations │              │
│ • Billing       │              │
└─────────────────┘              │
                                 ▼
                        ┌─────────────────┐
                        │ CloudFormation  │
                        │ Exports         │
                        │                 │
                        │ • HostedZoneId  │
                        │ • HostedZoneName│
                        └─────────────────┘
```

## Prerequisites

### AWS Account Setup

1. **AWS Account Contact Information**: Configure complete contact details at [AWS Account Settings](https://console.aws.amazon.com/billing/home#/account)
   - Full Name
   - Address (Line 1, City, State/Region, Postal Code, Country)
   - Phone Number

2. **AWS CLI Configuration**: 
   ```bash
   aws configure
   ```

3. **CDK Bootstrap** (if not already done):
   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

### Development Environment

- **Python 3.14+**
- **Node.js 18+** (for AWS CDK)
- **AWS CDK v2.225.0+**

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd 10ulabs.com
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK** (if not already installed):
   ```bash
   npm install -g aws-cdk
   ```

## Configuration

The project uses `config.json` for all configuration:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "budget_tokens": 10000,
      "max_tokens": 64000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  },
  "domain_name": "10ulabs.com"
}
```

### Key Configuration Options

- **`account_id`**: Target AWS account for deployment
- **`region`**: AWS region (Route53 Domains requires `us-east-1`)
- **`domain_name`**: Domain to register and manage
- **`bedrock`**: Configuration for future AI/ML integrations

## Deployment

### Deploy the Stack

```bash
# Review changes
cdk diff

# Deploy infrastructure
cdk deploy

# Monitor deployment progress
cdk deploy --verbose
```

### Domain Registration Process

The Lambda function automatically:

1. **Checks if domain is already registered**
   - If registered: Uses existing hosted zone
   - If not registered: Proceeds with registration

2. **Gathers contact information** from:
   - AWS Organizations (if available)
   - AWS Account billing contact
   - AWS Account contact information

3. **Registers domain** with:
   - 1-year initial registration
   - Auto-renewal enabled
   - Privacy protection for all contacts
   - All contact types (Admin, Tech, Billing, Registrant) set to account info

4. **Waits for hosted zone creation** (up to 14 minutes)

5. **Returns hosted zone details** for DNS management

## Outputs

After successful deployment, the stack provides:

- **`DomainName`**: Registered domain name
- **`HostedZoneId`**: Route53 Hosted Zone ID for DNS management
- **`HostedZoneName`**: Route53 Hosted Zone Name
- **`NameServers`**: Authoritative name servers for the domain
- **`RegistrationStatus`**: Current domain registration status

### CloudFormation Exports

For integration with other stacks:
- **`10ulabs-com-HostedZoneId`**: Hosted zone ID export
- **`10ulabs-com-HostedZoneName`**: Hosted zone name export

## CloudTrail Features

### Comprehensive Logging
- **Multi-region trail** capturing all AWS API calls
- **Global service events** included (IAM, CloudFront, etc.)
- **Management events** (read and write operations)

### Secure Storage
- **S3 bucket** with AES-256 encryption
- **Access logging** to separate S3 bucket
- **Public access blocked** on all buckets
- **SSL enforcement** via bucket policies

### Cost Optimization
- **Glacier transition** after 90 days for access logs
- **Log expiration** after 5 years (1,825 days)
- **CloudWatch Logs** retention: 1 year

### Real-time Monitoring
- **CloudWatch Logs integration** for real-time analysis
- **Log streams** automatically created
- **Structured JSON logging** for easy parsing

## Testing

The project includes comprehensive test coverage:

### Run All Tests
```bash
# Unit tests
python -m pytest test/cloudtrail_and_domain_name/test_unit.py -v

# Integration tests (requires deployed stack)
python -m pytest test/cloudtrail_and_domain_name/test_integration.py -v

# End-to-end tests (requires deployed stack)
python -m pytest test/cloudtrail_and_domain_name/test_e2e.py -v
```

### Test Categories

- **Unit Tests**: CDK template validation, Lambda function logic
- **Integration Tests**: Deployed resource verification
- **End-to-End Tests**: DNS resolution and functionality

## Troubleshooting

### Domain Registration Issues

**Problem**: Domain registration fails with payment error
```
Error: Payment method not configured
```
**Solution**: Configure a valid payment method in AWS Billing console

**Problem**: Missing contact information error
```
Error: AWS account missing contact fields: AddressLine1, City
```
**Solution**: Complete contact information at [AWS Account Settings](https://console.aws.amazon.com/billing/home#/account)

**Problem**: Domain not available
```
Error: Domain 10ulabs.com is not available: UNAVAILABLE
```
**Solution**: Domain is already registered (possibly by this account) or taken by another registrar

### CloudTrail Issues

**Problem**: CloudTrail not logging events
**Solution**: 
1. Verify trail is enabled: `aws cloudtrail get-trail-status --name TRAIL_NAME`
2. Check IAM permissions for CloudTrail service role
3. Verify S3 bucket permissions

**Problem**: High CloudTrail costs
**Solution**:
1. Review data events configuration (only management events are captured by default)
2. Check S3 lifecycle policies are working
3. Monitor CloudWatch Logs retention settings

### Lambda Function Issues

**Problem**: Lambda timeout during domain registration
```
Error: Task timed out after 900.00 seconds
```
**Solution**: 
1. Re-deploy stack - registration may have succeeded
2. Check Route53 console for hosted zone creation
3. Verify AWS account has proper permissions

**Problem**: Contact information validation fails
**Solution**:
1. Ensure phone number format is valid for the country
2. Verify all required contact fields are populated
3. Check country code is supported by Route53 Domains

### Stack Deployment Issues

**Problem**: CDK deployment fails with permission errors
**Solution**:
1. Verify AWS CLI credentials: `aws sts get-caller-identity`
2. Ensure CDK is bootstrapped: `cdk bootstrap`
3. Check IAM permissions for CDK deployment

**Problem**: Custom resource fails during stack deletion
**Solution**:
1. Domain deletion is not performed automatically (by design)
2. Manually delete hosted zone if needed: `aws route53 delete-hosted-zone`
3. Contact AWS support for domain transfer/deletion

## Project Structure

```
.
├── app.py                     # CDK application entry point
├── stack.py                   # Main infrastructure stack
├── config.json               # Configuration file
├── cdk.json                  # CDK settings
├── requirements.txt          # Python dependencies
├── lambda/
│   ├── handler.py           # Domain registration Lambda
│   └── cfnresponse.py       # CloudFormation response handling
└── test/
    └── cloudtrail_and_domain_name/
        ├── conftest.py      # Test configuration
        ├── stub.py          # Test stubs
        ├── test_unit.py     # Unit tests
        ├── test_integration.py # Integration tests
        └── test_e2e.py      # End-to-end tests
```

### Key Components

- **`DomainStack`**: Main CDK stack containing all infrastructure
- **`DomainRegistrationHandler`**: Lambda function for domain operations
- **CloudTrail Trail**: Multi-region audit logging
- **S3 Buckets**: CloudTrail storage and access logging
- **CloudWatch Logs**: Real-time log analysis
- **Route53 Hosted Zone**: DNS management

## Security Considerations

### Data Protection
- All S3 buckets use **AES-256 encryption**
- **Access logging** enabled for audit trails
- **Public access blocked** on all storage resources
- **SSL/TLS enforcement** via bucket policies

### Access Control
- **Least privilege IAM policies** for Lambda function
- **Resource-specific permissions** (no wildcard access)
- **Service-linked roles** for AWS service integration

### Privacy
- **Domain privacy protection** enabled for all contact types
- **Contact information** sourced from AWS account settings
- **No hardcoded credentials** in source code

## Cost Optimization

### Storage Costs
- **Lifecycle policies** transition logs to Glacier after 90 days
- **Automatic expiration** after 5 years
- **Versioning disabled** on buckets to reduce storage

### Operational Costs
- **CloudWatch Logs retention** limited to 1 year
- **Management events only** (no data events) in CloudTrail
- **Regional deployment** to minimize data transfer

### Monitoring
Use AWS Cost Explorer to monitor:
- S3 storage costs (CloudTrail logs)
- CloudWatch Logs ingestion and storage
- Route53 hosted zone charges
- Domain registration annual fees
