# 10ulabs.com Domain Infrastructure

AWS CDK infrastructure for automatically registering and managing the 
10ulabs.com domain name with Route53 hosted zone creation and CloudTrail 
auditing.

## Overview

This infrastructure stack provides automated domain registration and DNS 
management for the 10ulabs.com domain. It automatically registers the domain 
if not already registered, creates a Route53 hosted zone, and sets up 
comprehensive CloudTrail logging for audit and compliance purposes.

## Key Features

- **Automated Domain Registration**: Automatically checks domain availability
  and registers the domain if not already registered
- **Route53 Integration**: Creates and manages hosted zone for DNS records
- **Contact Information Integration**: Uses AWS account contact information
  for domain registration
- **CloudTrail Auditing**: Comprehensive logging of all domain-related
  activities
- **Privacy Protection**: Automatically enables WHOIS privacy protection
- **Auto-Renewal**: Configures automatic domain renewal

## AWS Resources Created

The stack creates the following AWS resources:

- **Route53 Domain Registration**: Registers the 10ulabs.com domain
- **Route53 Hosted Zone**: DNS zone for managing domain records
- **Lambda Function**: Custom resource handler for domain registration
- **CloudTrail**: Multi-region trail for audit logging
- **CloudWatch Log Group**: Stores CloudTrail logs with 1-year retention
- **S3 Buckets**: 
  - CloudTrail log storage bucket
  - Access log bucket for CloudTrail bucket
- **IAM Policies**: Permissions for Lambda function operations

## Prerequisites

### System Dependencies

- **Node.js**: Required for AWS CDK (version 18.x or later recommended)
- **Python 3.11+**: For running the CDK application
- **Git**: For version control operations

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages (from requirements.txt):

- `aws-cdk-lib==2.150.0`
- `constructs>=10.0.0,<11.0.0`
- `boto3>=1.34.0`
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`

### AWS Account Setup

Your AWS account must have complete contact information configured:

1. Navigate to the AWS Billing Console
2. Go to Account Settings
3. Ensure all contact fields are filled out:
   - Full Name
   - Address Line 1
   - City
   - State/Region
   - Country Code
   - Postal Code
   - Phone Number

### AWS Permissions

The deployment requires permissions for:

- Route53 domain registration and hosted zone management
- Lambda function creation and execution
- CloudTrail and CloudWatch Logs management
- S3 bucket creation and management
- IAM policy management
- AWS Account and Organizations read access

## Configuration

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
  "domain_name": "10ulabs.com"
}
```

### cdk.json

CDK-specific configuration with feature flags and context:

- **App Command**: `python3 app.py`
- **Watch Configuration**: Monitors file changes for hot reloading
- **CDK Feature Flags**: Enables latest CDK features and behaviors

## Usage Instructions

### Initial Setup

1. **Clone and navigate to the project**:

   ```bash
   git clone <repository-url>
   cd 10ulabs.com
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   npm install -g aws-cdk
   ```

3. **Configure AWS credentials**:

   Ensure your AWS credentials are configured through one of:
   - AWS credentials file (`~/.aws/credentials`)
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - IAM role (for EC2/Lambda execution)
   - AWS SSO

### Deployment

1. **Bootstrap CDK** (first-time only):

   ```bash
   cdk bootstrap aws://781581267945/us-east-1
   ```

2. **Deploy the infrastructure**:

   ```bash
   cdk deploy TenULabsDomainName
   ```

3. **Monitor the deployment**:

   The deployment will:
   - Check if the domain is already registered
   - Register the domain if not already owned
   - Wait for AWS to create the hosted zone
   - Output the hosted zone ID and name servers

### Using the Deployed Resources

After successful deployment, you can:

1. **View hosted zone details**:

   ```bash
   aws route53 get-hosted-zone --id <HostedZoneId>
   ```

2. **Add DNS records**:

   ```bash
   aws route53 change-resource-record-sets --hosted-zone-id <HostedZoneId> \
     --change-batch file://change-batch.json
   ```

3. **Check domain status**:

   ```bash
   aws route53domains get-domain-detail --domain-name 10ulabs.com
   ```

## Architecture Overview

### Component Interaction

```
Domain Registration Request
    ↓
Lambda Handler (Custom Resource)
    ↓
Route53 Domains API → Domain Registration
    ↓
AWS Auto-Creates → Route53 Hosted Zone
    ↓
CDK References → Hosted Zone for DNS Management
```

### Authentication and Authorization Flow

1. **Lambda Execution**: Uses IAM role with specific permissions
2. **Route53 Domains**: Requires us-east-1 region for domain operations
3. **Account Integration**: Reads AWS account contact information
4. **Organizations**: Attempts to read organization email for contacts

### Data Flows

1. **Domain Check**: Lambda checks domain availability/registration status
2. **Contact Retrieval**: Fetches AWS account contact information
3. **Registration**: Submits domain registration with contact details
4. **Zone Creation**: AWS automatically creates hosted zone
5. **Reference**: CDK creates reference to hosted zone for DNS management

### CloudTrail Integration

All domain-related activities are logged to CloudTrail:

- Domain registration operations
- DNS record changes
- Hosted zone modifications
- Lambda function executions

## Security Considerations

### Domain Security

- **Privacy Protection**: Automatically enabled for all contact types
- **Auto-Renewal**: Prevents accidental domain expiration
- **DNSSEC**: Can be enabled post-deployment if required

### Infrastructure Security

- **IAM Least Privilege**: Lambda function has minimal required permissions
- **Encryption**: All S3 buckets use server-side encryption
- **SSL Enforcement**: All S3 buckets require SSL for access
- **Access Logging**: CloudTrail bucket has separate access log bucket

### Monitoring and Auditing

- **Multi-Region Trail**: Captures activities across all AWS regions
- **CloudWatch Integration**: Structured logging with 1-year retention
- **Global Service Events**: Includes IAM, Route53, and other global services

## Troubleshooting

### Common Issues

1. **Domain Registration Timeout**:

   ```
   Error: Hosted zone not created within timeout period
   ```

   **Solution**: AWS may take up to 15 minutes to create the hosted zone.
   Wait and re-deploy the stack.

2. **Missing Contact Information**:

   ```
   Error: AWS account missing contact fields
   ```

   **Solution**: Configure complete contact information in AWS Account 
   Settings at <https://console.aws.amazon.com/billing/home#/account>

3. **Domain Already Registered Elsewhere**:

   ```
   Error: Domain 10ulabs.com is not available
   ```

   **Solution**: Transfer the domain to Route53 or update the configuration
   to use a different domain name.

### Debug Commands

1. **Check Lambda logs**:

   ```bash
   aws logs describe-log-groups --log-group-name-prefix \
     /aws/lambda/TenULabsDomainName
   ```

2. **View CloudFormation events**:

   ```bash
   aws cloudformation describe-stack-events --stack-name TenULabsDomainName
   ```

3. **Check domain registration operation**:

   ```bash
   aws route53domains get-operation-detail --operation-id <OperationId>
   ```

### Resource Cleanup

To remove all resources:

```bash
cdk destroy TenULabsDomainName
```

**Note**: Domain registration is not automatically cancelled. You must 
manually manage domain renewal/cancellation through the Route53 console.

## Output Values

The stack provides the following outputs:

- **DomainName**: The registered domain name (10ulabs.com)
- **HostedZoneId**: Route53 hosted zone identifier
- **HostedZoneName**: Route53 hosted zone name
- **NameServers**: Comma-separated list of authoritative name servers
- **RegistrationStatus**: Current domain registration status

These outputs are also exported for use by other CloudFormation stacks
with the prefix `10ulabs-com-`.
