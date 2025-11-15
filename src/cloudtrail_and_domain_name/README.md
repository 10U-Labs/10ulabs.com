# 10U Labs Domain Infrastructure

This AWS CDK infrastructure automates the registration and management of the
10ulabs.com domain using AWS Route53. It provides a complete solution for
domain registration, DNS hosting, and CloudTrail logging for compliance and
auditing purposes.

## Purpose and Key Features

- **Automated domain registration** - Registers domains through AWS Route53
  Domains service
- **DNS hosting** - Creates and manages Route53 hosted zones
- **Contact information integration** - Uses AWS account contact details for
  domain registration
- **CloudTrail logging** - Comprehensive audit logging for all AWS API calls
- **Compliance ready** - S3 lifecycle policies and log retention for
  regulatory requirements
- **Multi-region support** - CloudTrail configured for global service events

## Resources Created

This infrastructure deploys the following AWS resources:

### Route53 Resources

- **Hosted Zone** - DNS hosting for the specified domain
- **Domain Registration** - Automated domain registration via custom Lambda

### Lambda Resources

- **Domain Registration Handler** - Custom Lambda function that handles domain
  registration workflow
- **IAM Role** - Lambda execution role with required permissions

### S3 Resources

- **CloudTrail Bucket** - Primary storage for CloudTrail logs
- **Access Log Bucket** - Server access logs for CloudTrail bucket
- **Lifecycle Rules** - Automatic transition to Glacier after 90 days,
  deletion after 5 years

### CloudWatch Resources

- **Log Group** - CloudWatch logs for CloudTrail events (1 year retention)

### CloudTrail Resources

- **Multi-region Trail** - Global API activity logging with management events

## Prerequisites and Requirements

### System Dependencies

- **Node.js** (version 18 or later) - Required for AWS CDK
- **Python** (version 3.8 or later) - Required for CDK Python constructs
- **Git** - For cloning and version control

### Python Dependencies

Install the following packages from `requirements.txt`:

```txt
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[route53,route53domains,account,organizations]>=1.34.0
```

### AWS Account Prerequisites

1. **AWS Account Contact Information** - Complete contact details must be
   configured in AWS account settings
2. **Billing Information** - Valid payment method for domain registration fees
3. **IAM Permissions** - Deployment requires administrative access to:
   - Route53 and Route53 Domains
   - Lambda and IAM
   - S3 and CloudTrail
   - CloudWatch Logs
   - Account and Organizations APIs

## Configuration

Create a `config.json` file in the project root:

```json
{
  "domain_name": "10ulabs.com",
  "aws": {
    "account_id": "123456789012",
    "region": "us-east-1"
  }
}
```

### Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `domain_name` | Domain to register/manage | `"10ulabs.com"` |
| `aws.account_id` | AWS account ID | `"123456789012"` |
| `aws.region` | Primary AWS region | `"us-east-1"` |

## Usage Instructions

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd 10ulabs.com
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI**:

   ```bash
   npm install -g aws-cdk
   ```

4. **Configure AWS credentials** using AWS SDK authentication methods

5. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap
   ```

### Deployment

1. **Synthesize CloudFormation template**:

   ```bash
   cdk synth
   ```

2. **Deploy the infrastructure**:

   ```bash
   cdk deploy TenULabsDomainName
   ```

3. **Monitor deployment** - Domain registration may take several minutes

### Using the Deployed Resources

Once deployed, you can:

- **Access hosted zone** via AWS Route53 console
- **Create DNS records** using the hosted zone ID from stack outputs
- **Monitor domain status** through Route53 Domains console
- **Review API activity** in CloudTrail logs

## Architecture Overview

### Component Interactions

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK App       │───▶│  Custom Resource │───▶│  Lambda Handler │
│   (app.py)      │    │  (Domain Reg)    │    │  (handler.py)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Route53        │    │  CloudFormation  │    │  Route53        │
│  Hosted Zone    │◀───│  Stack           │    │  Domains API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  DNS Records    │    │  CloudTrail      │
│  (External)     │    │  Logging         │
└─────────────────┘    └──────────────────┘
```

### Authentication and Authorization

- **Lambda Execution Role** - Grants permissions for domain registration APIs
- **CloudTrail Service Role** - Allows writing logs to S3 and CloudWatch
- **Account API Access** - Retrieves contact information for domain
  registration

### Data Flows

1. **Domain Registration Flow**:
   - Custom resource triggers Lambda function
   - Lambda checks if domain exists or needs registration
   - Uses AWS account contact info for registration
   - Waits for hosted zone creation
   - Returns hosted zone details to CloudFormation

2. **Logging Flow**:
   - CloudTrail captures all AWS API calls
   - Logs stored in S3 with lifecycle management
   - Real-time logs sent to CloudWatch Log Group

## Security Considerations

### Data Protection

- **S3 Encryption** - All buckets use server-side encryption
- **SSL Enforcement** - HTTPS required for all S3 operations
- **Public Access Blocked** - S3 buckets deny all public access

### Access Control

- **Least Privilege** - Lambda role has minimal required permissions
- **Privacy Protection** - Domain registration includes WHOIS privacy
- **Log Retention** - CloudWatch logs retained for compliance (1 year)

### Monitoring

- **CloudTrail** - Comprehensive API activity logging
- **Multi-region** - Global service events captured
- **Lifecycle Management** - Automatic log archival and deletion

## Troubleshooting

### Common Issues

**Domain Registration Timeout**:

- Domain registration can take 15+ minutes
- Re-deploy stack if hosted zone creation times out
- Check Route53 Domains console for registration status

**Contact Information Errors**:

- Ensure AWS account contact details are complete
- Configure at: <https://console.aws.amazon.com/billing/home#/account>
- Include all required fields: name, address, phone, email

**Permission Errors**:

- Verify IAM permissions for Route53, Lambda, and Account APIs
- Route53 Domains operations require `us-east-1` region
- Organizations API access needed for root account email

**Lambda Timeout**:

- Domain registration may exceed default timeout
- Function configured for 15-minute maximum timeout
- Check CloudWatch logs for detailed error information

### Debugging Steps

1. **Check CloudFormation Events** - Review stack deployment progress
2. **Review Lambda Logs** - CloudWatch logs contain detailed operation info
3. **Verify Account Setup** - Ensure billing and contact info configured
4. **Check Domain Status** - Use Route53 Domains console for registration
   status
