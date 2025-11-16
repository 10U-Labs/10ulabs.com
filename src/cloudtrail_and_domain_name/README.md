# 10U Labs Domain Infrastructure

This AWS CDK infrastructure automatically provisions and manages the
10ulabs.com domain registration and Route53 hosted zone. It provides a
complete solution for domain management including registration, DNS
hosting, and comprehensive audit logging.

## Purpose and Key Features

- **Automated Domain Registration**: Automatically registers the domain
  if not already registered, using AWS account contact information
- **Route53 Hosted Zone Management**: Creates and manages DNS hosting
  for the domain
- **CloudTrail Audit Logging**: Comprehensive logging of all domain
  and DNS management activities
- **Smart Domain Detection**: Handles both new domain registration and
  existing domain scenarios
- **Privacy Protection**: Enables WHOIS privacy protection for all
  domain contacts
- **Auto-renewal**: Configures automatic domain renewal to prevent
  expiration

## Resources Created

This infrastructure creates the following AWS resources:

- **Route53 Hosted Zone**: DNS hosting for 10ulabs.com domain
- **Domain Registration**: AWS Route53 domain registration (if needed)
- **Lambda Function**: Custom resource handler for domain operations
- **CloudTrail**: Multi-region audit trail for domain activities
- **S3 Buckets**: 
  - CloudTrail log storage bucket
  - Access log bucket for audit trail
- **CloudWatch Log Group**: CloudTrail log aggregation and retention
- **IAM Roles/Policies**: Permissions for Lambda domain operations

## Prerequisites and Requirements

### System Dependencies

- **Node.js** (v14 or later): Required for AWS CDK
- **Python** (3.11 or later): Runtime for the infrastructure code
- **Git**: For repository management

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0`: AWS CDK core library
- `constructs>=10.0.0,<11.0.0`: CDK constructs framework
- `boto3>=1.34.0`: AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`:
  Type hints for AWS services

### AWS Prerequisites

- **AWS Account**: Active AWS account with appropriate permissions
- **Complete Account Contact Information**: Required for domain
  registration at <https://console.aws.amazon.com/billing/home#/account>
- **AWS Credentials**: Configured via AWS credentials file, environment
  variables, or IAM roles
- **CDK Bootstrap**: Run `cdk bootstrap` in your AWS account/region

## Configuration

### config.json

The main configuration file defines AWS settings and domain name:

```json
{
  "aws": {
    "account_id": 781581267945,
    "bedrock": {
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "region": "us-east-1"
  },
  "domain_name": "10ulabs.com"
}
```

### cdk.json

CDK configuration file with feature flags and watch settings:

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
  }
}
```

## Usage Instructions

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd 10ulabs.com
   ```

2. **Install dependencies**:

   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install Node.js dependencies (if package.json exists)
   npm install
   ```

3. **Configure AWS credentials**:

   ```bash
   # Option 1: AWS credentials file
   aws configure
   
   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Bootstrap CDK** (first time only):

   ```bash
   cdk bootstrap
   ```

### Deployment

1. **Review the deployment plan**:

   ```bash
   cdk diff
   ```

2. **Deploy the infrastructure**:

   ```bash
   cdk deploy
   ```

3. **Monitor the deployment**: The Lambda function will automatically:
   - Check if domain is already registered
   - Register domain if needed (takes 5-15 minutes)
   - Wait for hosted zone creation
   - Configure nameservers

### Using the Deployed Resources

After successful deployment, you can:

1. **Manage DNS records** via Route53 console or CDK
2. **View domain status** in Route53 Domains console
3. **Monitor activities** via CloudTrail logs
4. **Access outputs**:
   - Hosted Zone ID for cross-stack references
   - Nameservers for external configuration
   - Domain registration status

### Scripts

The repository includes a comprehensive README generation script:

```bash
# Check if README needs updating
python scripts/readme.py --check --project-dir . --aws-region us-east-1

# Update README
python scripts/readme.py --update --project-dir . --aws-region us-east-1
```

## Architecture Overview

### Component Interaction Flow

1. **CDK App** (`app.py`) loads configuration and initializes the stack
2. **Domain Stack** (`stack.py`) creates all AWS resources
3. **Custom Resource** triggers Lambda function for domain operations
4. **Lambda Handler** (`lambda/handler.py`) performs domain registration
5. **Route53** hosts DNS records for the domain
6. **CloudTrail** logs all domain and DNS activities

### Authentication and Authorization

- **Lambda Execution Role**: IAM role with permissions for:
  - Route53 Domains API operations
  - Route53 hosted zone management
  - AWS Account contact information access
  - AWS Organizations API access
- **Cross-Service Permissions**: CloudTrail service-linked roles for
  S3 bucket access and CloudWatch Logs

### Data Flows

1. **Domain Registration Flow**:
   ```
   Custom Resource → Lambda → Route53 Domains API → Domain Registration
   ```

2. **DNS Management Flow**:
   ```
   CDK Stack → Route53 Hosted Zone → DNS Records → Public DNS
   ```

3. **Audit Flow**:
   ```
   AWS API Calls → CloudTrail → S3 Bucket → CloudWatch Logs
   ```

## Security Considerations

- **Privacy Protection**: WHOIS privacy enabled for all contacts
- **Audit Logging**: All domain operations logged via CloudTrail
- **Secure Storage**: S3 buckets configured with:
  - Server-side encryption (SSE-S3)
  - Block public access
  - SSL enforcement
  - Access logging
- **Least Privilege**: Lambda function has minimal required permissions
- **Multi-Region Logging**: CloudTrail captures global service events
- **Log Retention**: CloudWatch logs retained for 1 year
- **Lifecycle Management**: S3 objects archived to Glacier after 90 days

## Troubleshooting

### Common Issues

1. **Domain registration timeout**:
   - Re-run `cdk deploy` after 15-30 minutes
   - Check CloudTrail logs for registration status

2. **Missing account contact information**:
   - Complete AWS account contact info at billing console
   - Ensure all required fields are populated

3. **Permission errors**:
   - Verify IAM permissions for domain operations
   - Check AWS credentials configuration

4. **Hosted zone not found**:
   - Wait for AWS to create hosted zone after registration
   - Check Route53 console for zone creation status

### Debugging Commands

```bash
# View CDK outputs
cdk list
cdk synthesize

# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix="/aws/lambda/TenULabs"

# Verify domain status
aws route53domains get-domain-detail --domain-name 10ulabs.com --region us-east-1

# Check hosted zone
aws route53 list-hosted-zones-by-name --dns-name 10ulabs.com
```

### Stack Dependencies

The infrastructure includes dependency management to ensure:

- CloudTrail is created before domain operations
- Hosted zone is available before stack outputs
- Proper cleanup order during stack deletion
