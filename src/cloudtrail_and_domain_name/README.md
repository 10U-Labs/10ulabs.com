# AWS CDK Domain Registration and CloudTrail Infrastructure

## Overview

This AWS CDK infrastructure automates the registration of domain names via Route53 and establishes comprehensive audit logging through AWS CloudTrail. It provides a complete solution for domain acquisition, hosted zone creation, and organizational activity monitoring with a serverless architecture.

The infrastructure uses AWS Lambda as a custom CloudFormation resource to intelligently handle domain registration, automatically detecting existing registrations and creating Route53 hosted zones while maintaining full audit trails of all AWS API activities.

## Purpose and Key Features

### Core Capabilities

- **Automated Domain Registration**: Seamlessly register domain names using AWS Route53 Domains API
- **Intelligent Domain Detection**: Checks for existing domain registrations before attempting new registrations
- **Auto-hosted Zone Creation**: Automatically creates and configures Route53 hosted zones post-registration
- **Comprehensive Audit Logging**: Tracks all AWS API calls across regions and services
- **Secure Log Storage**: Implements S3 lifecycle policies and encryption for audit logs
- **CloudWatch Integration**: Streams CloudTrail logs to CloudWatch Logs for real-time analysis
- **Multi-region Monitoring**: Captures global service events and management activities

### Automation Features

- Automatic contact information retrieval from AWS Account and Organizations APIs
- Phone number formatting based on country-specific dialing codes
- Privacy protection enabled by default for domain contacts
- Automatic 1-year domain renewal configuration
- Exponential backoff retry logic for hosted zone availability checks

## Resources Created

### CloudTrail Configuration

```
DomainCloudTrail (Multi-region Trail)
├── Event Types: All management events (READ and WRITE)
├── Global Events: Enabled
├── CloudWatch Logs: Enabled (1-year retention)
└── S3 Bucket: Versioned, encrypted, access-logged
```

**CloudTrail Trail Properties**:
- Multi-region deployment for organization-wide visibility
- Captures all management events (both read and write operations)
- Includes global service events (IAM, CloudFront, Route53, etc.)
- Sends logs to both S3 and CloudWatch Logs simultaneously
- 1-year log retention in CloudWatch

### S3 Buckets

#### CloudTrail Bucket (`CloudTrailBucket`)
- **Purpose**: Primary storage for CloudTrail logs
- **Features**:
  - S3-managed server-side encryption (SSE-S3)
  - Public access completely blocked
  - Automatic deletion on stack removal
  - Server access logging enabled
  - SSL/TLS enforcement for all connections
  - Versioning disabled for cost optimization

#### Access Log Bucket (`CloudTrailAccessLogBucket`)
- **Purpose**: Stores access logs from the CloudTrail bucket
- **Features**:
  - S3-managed encryption
  - Public access completely blocked
  - Retained on stack deletion (compliance requirement)
  - SSL/TLS enforcement
  - Lifecycle policy:
    - Transitions to Glacier storage after 90 days
    - Automatic expiration after 5 years (1825 days)

### Lambda Function

#### DomainRegistrationHandler
- **Runtime**: Python 3.11
- **Timeout**: 900 seconds (15 minutes)
- **Trigger**: CloudFormation custom resource
- **IAM Permissions**:
  - Route53 Domains API (CheckDomainAvailability, RegisterDomain, GetDomainDetail, GetOperationDetail)
  - Route53 API (ListHostedZonesByName, GetHostedZone, CreateHostedZone)
  - Account API (GetContactInformation, GetAlternateContact)
  - Organizations API (DescribeOrganization)

### CloudFormation Custom Resource

The `DomainRegistration` custom resource orchestrates the entire domain registration workflow:
- Depends on CloudTrail trail for audit compliance
- Returns hosted zone ID, name servers, and domain status
- Supports both creation and update operations
- Gracefully handles deletion (no-op)

## Prerequisites and Requirements

### AWS Account Requirements

- AWS Account with appropriate IAM permissions
- AWS Organizations configured (optional, but recommended for email retrieval)
- AWS Billing contact information fully configured at https://console.aws.amazon.com/billing/home#/account

### Required Contact Information

The following fields must be configured in your AWS Account:
- **FullName**: Account holder's full name
- **AddressLine1**: Street address
- **City**: City name
- **StateOrRegion**: State or region code
- **CountryCode**: ISO 3166-1 alpha-2 country code
- **PostalCode**: Postal/ZIP code
- **PhoneNumber**: Contact phone number

If not configured, the Lambda function will fail with specific field requirements.

### Software Requirements

- Python 3.9 or later
- AWS CDK v2.x
- AWS CLI v2
- boto3 library for Lambda handler
- Node.js 14+ (CDK runtime requirement)

### IAM Permissions Required

Your deployment user/role must have permissions for:
- CloudTrail management
- S3 bucket creation and management
- Lambda function creation
- IAM role and policy creation
- Route53 and Route53 Domains operations
- CloudWatch Logs creation

## Usage Instructions

### Step 1: Configure AWS Account Contact Information

Before deploying, ensure your AWS account has complete contact information:

```bash
# Visit AWS Console
https://console.aws.amazon.com/billing/home#/account

# Or use AWS CLI to verify
aws account get-contact-information --region us-east-1
```

### Step 2: Prepare Configuration

Create a configuration file with your desired domain name:

```python
# config.py
config = {
    "domain_name": "example.com"
}
```

### Step 3: Deploy the Stack

```bash
# Install CDK dependencies
pip install -r requirements.txt

# Synthesize the CDK app
cdk synth

# Deploy to AWS
cdk deploy --require-approval=never

# Or with specific configuration
cdk deploy \
  -c domain_name=mydomain.com \
  --require-approval=never
```

### Step 4: Monitor Deployment

The deployment typically takes 2-5 minutes. CloudTrail will be active immediately, but domain registration may take additional time:

```bash
# View stack outputs
aws cloudformation describe-stacks \
  --stack-name DomainStack \
  --query 'Stacks[0].Outputs'

# Check Lambda execution logs
aws logs tail /aws/lambda/DomainRegistrationHandler --follow

# Check CloudTrail status
aws cloudtrail describe-trails --trail-name-list DomainCloudTrail
```

### Step 5: Verify Domain Registration

```bash
# Check domain status
aws route53domains get-domain-detail --domain-name example.com --region us-east-1

# List hosted zones
aws route53 list-hosted-zones-by-name --dns-name example.com
```

## Architecture Explanation

### Domain Registration Workflow

```
CloudFormation Create Event
        ↓
Lambda Handler Invoked
        ↓
    ┌───────────────────┐
    │ Check if domain   │
    │ already exists    │
    └───────────────────┘
         ↙         ↖
    YES │          │ NO
        ↓          ↓
   Return Zone   Register New Domain
   Attributes        ↓
        │       Get Contact Info
        │            ↓
        │       Check Availability
        │            ↓
        │       Submit Registration
        │            ↓
        │       Poll for Hosted Zone
        │            ↓
        │       Return Zone Attributes
        └───────────┬──────────────┘
                    ↓
            CFN Custom Resource
                 Outputs
```

### CloudTrail Configuration Details

**Event Flow**:
1. All AWS API calls are captured by CloudTrail
2. Events are written to S3 (primary storage)
3. Events are simultaneously streamed to CloudWatch Logs
4. Access logs for the CloudTrail bucket are written to the access log bucket
5. Logs transition to Glacier after 90 days for cost optimization
6. Logs expire after 5 years (1825 days)

**Event Coverage**:
- Management events: All API calls (READ/WRITE)
- Global service events: IAM, CloudFront, Route53, etc.
- Multi-region: Events from all AWS regions
- Data events: Not captured (can be added if needed)

### Domain Registration Workflow

**Existing Domain Detection**:
- Lambda first attempts to retrieve existing domain details
- If found, returns hosted zone ID and name servers
- Skips registration process if domain already registered

**New Domain Registration**:
1. Retrieves contact information from AWS Account API
2. Falls back to Organizations API for email if available
3. Checks domain availability via Route53 Domains
4. Formats phone number based on country dialing codes
5. Submits registration with privacy protection enabled
6. Waits up to 14 minutes for hosted zone creation
7. Uses exponential backoff (2^n seconds) for retry attempts

**Contact Information Priority**:
1. Organization Master Account Email (if in AWS Organization)
2. Billing Alternate Contact Email (if configured)
3. Generated email from account name (fallback)

### Custom Resource Lifecycle

**Create Operation**:
- Triggers domain registration process
- Returns hosted zone ID for resource dependency
- Retries with exponential backoff for transient failures

**Update Operation**:
- Currently treated as no-op (domain name not updated)
- Returns existing hosted zone information

**Delete Operation**:
- No-op operation
- Domain remains registered (intentional for data protection)
- CloudTrail logs retained (compliance requirement)

## Configuration Details

### Environment Variables

```bash
# GitHub SHA for Lambda description (optional)
export GITHUB_SHA=abc123def456789

# AWS Region (CloudTrail bucket)
export AWS_REGION=us-east-1
```

### Stack Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `domain_name` | Yes | Domain to register | `example.com` |
| `construct_id` | No | CDK stack ID | `DomainStack` |

### Supported TLDs

Domain registration supports most Route53 Domains TLDs, including:
- `.com`, `.net`, `.org`, `.co`, `.io`
- Country-code TLDs: `.co.uk`, `.com.au`, `.de`, `.fr`, etc.
- New generic TLDs: `.app`, `.dev`, `.cloud`, `.tech`, etc.

Check availability in AWS Console for your specific TLD.

### Supported Countries

The Lambda function includes phone number formatting for 21 countries:

| Country | Code | Dialing Code |
|---------|------|--------------|
| United States | US | +1 |
| United Kingdom | GB | +44 |
| Germany | DE | +49 |
| France | FR | +33 |
| Japan | JP | +81 |
| Australia | AU | +61 |
| Canada | CA | +1 |
| Brazil | BR | +55 |
| India | IN | +91 |
| China | CN | +86 |

For countries not in the list, defaults to +1.

## Testing Approach

### Local Testing

```bash
# Run Lambda handler locally with test event
import json
from lambda.handler import handler

test_event = {
    "RequestType": "Create",
    "ResourceProperties": {
        "DomainName": "test.com"
    },
    "StackId": "arn:aws:cloudformation:...",
    "RequestId": "test-123",
    "LogicalResourceId": "DomainRegistration",
    "ResponseURL": "https://..."
}

# Requires AWS credentials configured
handler(test_event, None)
```

### Integration Testing

```bash
# Deploy to dev account
cdk deploy --context domain_name=test-example.com

# Verify CloudTrail is capturing events
aws cloudtrail lookup-events \
  --trail-name DomainCloudTrail \
  --max-results 10

# Check Lambda execution
aws logs tail /aws/lambda/DomainRegistrationHandler --follow

# Validate hosted zone
aws route53 list-hosted-zones
```

### CloudTrail Validation

```bash
# Verify trail is logging
aws cloudtrail get-trail-status --name DomainCloudTrail

# Query CloudTrail events
aws cloudtrail lookup-events \
  --event-source route53domains.amazonaws.com \
  --max-results 5

# View S3 bucket contents
aws s3 ls s3://cloudtrail-bucket/ --recursive

# Check CloudWatch Logs
aws logs tail /aws/cloudtrail/DomainCloudTrail --follow
```

### Failure Scenarios

**Test missing contact information**:
```bash
# Clear account contact info before deployment
# Expected: Lambda fails with specific missing fields error
```

**Test domain availability check**:
```bash
# Use a known taken domain (e.g., example.com)
cdk deploy -c domain_name=example.com
# Expected: Lambda returns availability error
```

**Test existing domain reuse**:
```bash
# Deploy with already-registered domain
# Expected: Lambda detects existing registration and returns zone info
```

## Security Considerations

### Bucket Security

**CloudTrail Bucket**:
- ✅ All public access blocked via `BlockPublicAccess`
- ✅ S3-managed encryption enabled (SSE-S3)
- ✅ SSL/TLS required for all connections (`enforce_ssl=True`)
- ✅ Automatic deletion on stack removal for ephemeral stacks
- ✅ Versioning disabled to reduce storage costs

**Access Log Bucket**:
- ✅ All public access blocked
- ✅ Encryption enabled
- ✅ Retained on deletion (prevents accidental data loss)
- ✅ SSL/TLS required

### CloudTrail Security

- ✅ Multi-region trail captures all regions
- ✅ Global service events included
- ✅ Integrated with CloudWatch Logs for real-time alerting
- ✅ Log file integrity validation enabled by default
- ✅ Automatic log compression and retention management

### Lambda Security

**IAM Least Privilege**:
- Lambda role includes only necessary Route53 Domains permissions
- Account and Organizations APIs restricted to read operations only
- No S3 access for Lambda execution role

**Data Sensitivity**:
- Contact information retrieved from AWS Account API
- Domain registration uses provided credentials
- All communications over HTTPS/TLS
- CloudTrail captures all Lambda invocations

**Secrets Management**:
- No hardcoded credentials
- Uses IAM roles for service authentication
- Account contact info retrieved from AWS Account API (not stored)

### Domain Privacy

**Privacy Protections Enabled**:
- Admin contact information hidden
- Registrant contact information hidden
- Tech contact information hidden
- Billing contact information hidden

**Contact Information Sources**:
1. AWS Account Contact Information (primary)
2. AWS Organizations Master Account Email (secondary)
3. AWS Billing Alternate Contact (tertiary)

### Audit and Compliance

- CloudTrail enabled for all management events
- Logs stored with encryption at rest
- Access logging for CloudTrail bucket itself
- 1-year retention in CloudWatch for analysis
- 5-year retention in S3 for compliance
- Glacier archival after 90 days for cost optimization

### Network Security

- No public endpoints exposed
- Private Lambda execution within VPC (if configured)
- All API calls to AWS services over HTTPS
- No cross-account access required

## Troubleshooting Tips

### Lambda Execution Failures

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/DomainRegistrationHandler --follow

# Or view specific log group
aws logs describe-log-streams \
  --log-group-name /aws/lambda/DomainRegistrationHandler

aws logs get-log-events \
  --log-group-name /aws/lambda/DomainRegistrationHandler \
  --log-stream-name 'stream-name'
```

**Common Errors**:

1. **"AWS account missing contact fields"**
   - Missing required information at https://console.aws.amazon.com/billing/home#/account
   - Add FullName, Address, City, State, Country, PostalCode, PhoneNumber

2. **"Domain is not available"**
   - Selected domain already registered
   - Try alternative domain name or different TLD

3. **"Hosted zone not created within timeout"**
   - AWS CloudFormation takes time to create hosted zone
   - Re-deploy stack after 5 minutes
   - Eventual consistency: Zone creation can take 10-15 minutes

4. **"InvalidInput" exception**
   - Domain name format invalid (e.g., missing TLD)
   - Verify domain name syntax

### CloudTrail Issues

**Trail not logging**:
```bash
# Check trail status
aws cloudtrail get-trail-status --name DomainCloudTrail

# Verify S3 bucket exists and is accessible
aws s3 ls s3://cloudtrail-bucket/

# Check CloudTrail permissions
aws cloudtrail describe-trails --include-shadow-trails
```

**Missing CloudWatch Logs**:
```bash
# Verify log group exists
aws logs describe-log-groups \
  --log-group-name-prefix /aws/cloudtrail/

# Check log retention
aws logs describe-log-groups \
  --log-group-name-prefix /aws/cloudtrail/

# View recent events
aws logs tail /aws/cloudtrail/DomainCloudTrail --follow
```

### Domain Registration Delays

**Hosted Zone Not Available**:
- Initial registration can take 5-15 minutes
- AWS automatically creates hosted zone during registration
- Re-deploy stack if zone not detected

**Verification Steps**:
```bash
# Check domain registration status
aws route53domains get-domain-detail \
  --domain-name example.com \
  --region us-east-1

# List all hosted zones
aws route53 list-hosted-zones

# Check CloudFormation stack events
aws cloudformation describe-stack-events \
  --stack-name DomainStack \
  --query 'StackEvents[*].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]'
```

### Contact Information Issues

**Generated Email Address Warning**:
```
WARNING: Generated email address: admin@example.com
Please update domain contacts after registration
```
- This occurs when no email found in Account/Billing/Organization
- Update contacts at https://console.aws.amazon.com/route53domains/

**Phone Number Formatting Errors**:
- Ensure phone number includes country dialing code
- Example: +1.2025551234 (US), +44.2071838750 (UK)
- Add phone number to account contact info if not present

### Stack Deletion Issues

**S3 Bucket Deletion Failed**:
- Access log bucket retained by design (RemovalPolicy.RETAIN)
- CloudTrail bucket auto-deletes (RemovalPolicy.DESTROY + auto_delete_objects=True)
- Manually delete access log bucket if needed:
  ```bash
  aws s3 rb s3://cloudtrail-access-log-bucket --force
  ```

**Domain Not Deleted**:
- Domain remains registered after stack deletion (by design)
- Prevents accidental domain loss
- Manually deregister if needed:
  ```bash
  aws route53domains delete-domain \
    --domain-name example.com \
    --region us-east-1
  ```

### Performance Optimization

**Reduce CloudTrail Log Volume**:
- Currently captures all management events
- Can exclude specific services if needed
- Glacier transition after 90 days reduces costs

**CloudWatch Logs Costs**:
- 1-year retention configured
- Adjust retention if needed:
  ```python
  retention=logs.RetentionDays.THREE_MONTHS
  ```

### Support Resources

- AWS CloudTrail Documentation: https://docs.aws.amazon.com/cloudtrail/
- Route53 Domains API: https://docs.aws.amazon.com/route53-domains/latest/APIReference/
- AWS CDK Reference: https://docs.aws.amazon.com/cdk/api/
- Lambda Timeout Adjustment: Update `Duration.seconds(900)` in stack.py
- Contact Information: https://console.aws.amazon.com/billing/home#/account