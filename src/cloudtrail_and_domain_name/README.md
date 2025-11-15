# 10U Labs Domain Management Infrastructure

This AWS CDK infrastructure project automates the registration and management
of the 10ulabs.com domain using AWS Route53 and Route53 Domains. It provides
a complete solution for domain registration with automatic hosted zone creation
and comprehensive CloudTrail logging for compliance and auditing.

## Purpose and Key Features

- **Automated Domain Registration**: Registers domains through AWS Route53
  Domains service with automatic contact information retrieval
- **Hosted Zone Management**: Creates and manages Route53 hosted zones for
  DNS management
- **Contact Information Integration**: Automatically uses AWS account contact
  information for domain registration
- **Compliance Logging**: Comprehensive CloudTrail logging for all domain
  and DNS operations
- **Security**: Privacy protection enabled for all domain contacts

## Resources Created

This infrastructure creates the following AWS resources:

### Core Domain Resources

- **Custom Lambda Function**: Handles domain registration and hosted zone
  creation logic
- **Route53 Hosted Zone**: DNS management for the registered domain
- **Custom CloudFormation Resource**: Orchestrates domain registration
  workflow

### Logging and Compliance

- **CloudTrail Trail**: Multi-region trail capturing all API calls
- **CloudWatch Log Group**: Stores CloudTrail logs with 1-year retention
- **S3 Bucket (CloudTrail)**: Primary storage for CloudTrail logs
- **S3 Bucket (Access Logs)**: Stores access logs for CloudTrail bucket

### Security and Lifecycle Management

- **IAM Policies**: Least-privilege permissions for Lambda function
- **S3 Lifecycle Rules**: Automatic archival to Glacier after 90 days,
  deletion after 5 years
- **Encryption**: S3-managed encryption for all storage resources

## Prerequisites and Requirements

### System Dependencies

- **Node.js** (v18 or later): Required for AWS CDK framework
- **Python** (3.11 or later): Runtime for the application and Lambda functions
- **Git**: For cloning and version control

### Python Dependencies

Install the required Python packages listed in `requirements.txt`:

```text
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[route53,route53domains,account,organizations]>=1.34.0
```

### AWS Prerequisites

- **AWS Account**: With appropriate permissions for domain registration
- **AWS Credentials**: Configured for CDK deployment
- **Account Contact Information**: Complete billing contact details required
  for domain registration
- **AWS Organizations** (optional): For automatic email address detection

## Configuration

Create a `config.json` file in the project root with the following structure:

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
| --------- | ----------- | ------- |
| `domain_name` | Domain to register/manage | `"10ulabs.com"` |
| `aws.account_id` | Target AWS account ID | `"123456789012"` |
| `aws.region` | AWS region for deployment | `"us-east-1"` |

## Installation and Usage

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

3. **Install AWS CDK** (if not already installed):

   ```bash
   npm install -g aws-cdk
   ```

4. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap
   ```

### Deployment

1. **Configure your domain settings** in `config.json`

2. **Deploy the infrastructure**:

   ```bash
   cdk deploy TenULabsDomainName
   ```

3. **Verify deployment**:

   ```bash
   cdk list
   cdk diff
   ```

### Post-Deployment

After successful deployment, the infrastructure outputs:

- **Domain Name**: The registered domain
- **Hosted Zone ID**: For DNS record management
- **Name Servers**: For external DNS delegation (if needed)
- **Registration Status**: Current domain status

## Architecture Overview

### Component Interactions

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDK App       │───▶│  Custom Resource │───▶│ Lambda Function │
│   (app.py)      │    │                  │    │   (handler.py)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                        ┌─────────────────────────────────┼─────────────────┐
                        │                                 ▼                 │
                        │    ┌─────────────────┐    ┌──────────────┐       │
                        │    │ Route53 Domains │    │   Route53    │       │
                        │    │   (Register)    │    │ (Hosted Zone)│       │
                        │    └─────────────────┘    └──────────────┘       │
                        │                                                   │
                        │    ┌─────────────────┐    ┌──────────────┐       │
                        │    │ Account Service │    │ Organizations │       │
                        │    │ (Contact Info)  │    │ (Email Info) │       │
                        │    └─────────────────┘    └──────────────┘       │
                        └───────────────────────────────────────────────────┘
                                             │
                        ┌─────────────────────────────────────────────────────┐
                        │                CloudTrail                          │
                        │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐│
                        │  │ CloudWatch  │  │      S3      │  │ Access Logs ││
                        │  │  Log Group  │  │   (Primary)  │  │   Bucket    ││
                        │  └─────────────┘  └──────────────┘  └─────────────┘│
                        └─────────────────────────────────────────────────────┘
```

### Workflow Process

1. **CDK Deployment**: Triggers custom resource creation
2. **Lambda Execution**: Handles domain registration logic
3. **Contact Retrieval**: Fetches AWS account contact information
4. **Domain Registration**: Registers domain with Route53 Domains
5. **Hosted Zone Creation**: AWS automatically creates hosted zone
6. **Zone Detection**: Lambda waits for and detects the new hosted zone
7. **Resource Completion**: Returns hosted zone details to CloudFormation

### Authentication Flow

- **Lambda Function**: Uses IAM role with specific Route53 and Account
  permissions
- **AWS Services**: Authentication via IAM roles and policies
- **Cross-Region**: Route53 Domains requires us-east-1 region access

## Security Considerations

### Domain Security

- **Privacy Protection**: Enabled for all contact types (admin, registrant,
  tech, billing)
- **Contact Information**: Uses AWS account contact details to prevent
  information leakage
- **Auto-Renewal**: Enabled to prevent accidental domain expiration

### Infrastructure Security

- **Least Privilege**: Lambda function has minimal required permissions
- **Encryption**: All S3 buckets use AWS-managed encryption
- **SSL Enforcement**: Required for all S3 bucket operations
- **Public Access**: Blocked on all S3 buckets

### Logging and Monitoring

- **CloudTrail**: Captures all API calls for audit compliance
- **Multi-Region**: Trail covers all AWS regions for comprehensive logging
- **Retention**: CloudWatch logs retained for 1 year, S3 logs for 5 years
- **Access Logging**: S3 bucket access separately logged for security analysis

## Troubleshooting

### Common Issues

#### Domain Registration Timeout

**Symptoms**: CloudFormation stack creation fails with timeout

**Solutions**:

   ```bash
   # Check registration status
   aws route53domains get-operation-detail --operation-id <operation-id>
   
   # Re-deploy after registration completes
   cdk deploy TenULabsDomainName
   ```

#### Missing Contact Information

**Symptoms**: Registration fails with contact validation errors

**Solutions**:

1. **Update AWS account contact information**:
   - Visit: <https://console.aws.amazon.com/billing/home#/account>
   - Complete all required fields

2. **Configure alternate billing contact**:

   ```bash
   aws account put-alternate-contact \
     --alternate-contact-type BILLING \
     --email-address admin@yourcompany.com \
     --name "Billing Admin" \
     --phone-number "+1.5551234567"
   ```

#### Hosted Zone Not Found

**Symptoms**: Domain registered but hosted zone missing

**Cause**: AWS takes time to create hosted zone after registration

**Solution**: Wait 10-15 minutes and re-deploy:

   ```bash
   cdk deploy TenULabsDomainName
   ```

#### Permission Errors

**Symptoms**: Access denied errors during deployment

**Required Permissions**:

- `route53domains:*`
- `route53:*`
- `account:GetContactInformation`
- `organizations:DescribeOrganization`
- `lambda:*`
- `iam:*`
- `s3:*`
- `cloudtrail:*`
- `logs:*`

### Debug Commands

```bash
# Check stack status
cdk list
cdk diff TenULabsDomainName

# View CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name TenULabsDomainName

# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# Verify domain status
aws route53domains get-domain-detail --domain-name 10ulabs.com
```
