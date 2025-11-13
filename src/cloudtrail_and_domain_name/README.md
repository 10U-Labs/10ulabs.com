# AWS CDK Domain Registration and CloudTrail Infrastructure

## Overview

This AWS CDK infrastructure provides a comprehensive solution for automated
domain registration and centralized audit logging through CloudTrail. It
combines AWS Route 53 domain management with multi-region CloudTrail logging
to create a secure, auditable infrastructure foundation for domain-based
deployments.

The stack automatically registers a domain name and creates an associated
Route 53 Hosted Zone, while simultaneously establishing CloudTrail logging
across all AWS regions for compliance and security monitoring.

## Purpose and Key Features

### Primary Objectives

- **Automated Domain Registration**: Programmatic domain registration via
AWS Route 53 Domains API
- **Centralized Audit Logging**: Comprehensive CloudTrail configuration
capturing all API activity
- **Infrastructure as Code**: Fully declarative AWS CDK implementation for
reproducible deployments
- **Compliance Ready**: Long-term log retention and archival policies for
regulatory requirements

### Key Features

- ✅ Multi-region CloudTrail with global service event tracking
- ✅ Automatic domain availability checking and registration
- ✅ Intelligent hosted zone detection and reuse
- ✅ CloudWatch Logs integration for real-time monitoring
- ✅ S3 lifecycle policies with Glacier archival after 90 days
- ✅ Server access logging for CloudTrail bucket operations
- ✅ Privacy protection on all domain contacts
- ✅ Automatic nameserver delegation configuration
- ✅ International phone number formatting support (24 countries)

## Resources Created

### CloudTrail Infrastructure

#### CloudTrail Bucket (`CloudTrailBucket`)

- **Purpose**: Primary storage for CloudTrail event logs
- **Configuration**:
  - S3-managed encryption enabled
  - Public access completely blocked
  - SSL/TLS enforcement required
  - Server access logging to separate access log bucket
  - Auto-deletion enabled for lifecycle management
  - Deletion policy: DESTROY (removed when stack is deleted)

#### Access Log Bucket (`CloudTrailAccessLogBucket`)

- **Purpose**: Capture access logs for CloudTrail bucket operations
- **Configuration**:
  - S3-managed encryption enabled
  - Public access completely blocked
  - SSL/TLS enforcement required
  - Lifecycle policy:
    - Transition to Glacier after 90 days (cost optimization)
    - Automatic deletion after 5 years (1,825 days)
  - Deletion policy: RETAIN (preserved for audit)

#### CloudTrail Logs (`CloudTrailLogGroup`)

- **Purpose**: CloudWatch Logs integration for real-time monitoring
- **Configuration**:
  - 1-year retention period
  - Retention policy: RETAIN (preserved after stack deletion)

#### Trail Configuration (`DomainCloudTrail`)

- **Features**:
  - Multi-region trail capturing events across all AWS regions
  - Global service events enabled (CloudFront, IAM, etc.)
  - Management events: ALL (read and write operations)
  - Real-time delivery to CloudWatch Logs
  - Automatic file validation for integrity verification

### Domain Registration Components

#### Lambda Function (`DomainRegistrationHandler`)

- **Runtime**: Python 3.11
- **Timeout**: 900 seconds (15 minutes)
- **Purpose**: Custom resource handler for domain registration workflow
- **Required IAM Permissions**:
  - Route 53 Domains API (check availability, register, get status)
  - Route 53 API (hosted zone management)
  - AWS Account API (contact information retrieval)
  - AWS Organizations API (organization details)

#### Custom Resource (`DomainRegistration`)

- **Service Token**: Domain registration Lambda function
- **Properties**: Domain name from configuration
- **Dependencies**: Ensures CloudTrail is fully deployed before
registration

#### Hosted Zone Reference (`HostedZone`)

- **Source**: Dynamically retrieved from domain registration
- **Attributes**: Hosted Zone ID and nameservers

### CloudFormation Outputs

| Output | Description | Export |
|--------|-------------|--------|
| `DomainName` | Registered domain name | — |
| `HostedZoneId` | Route 53 Hosted Zone ID | `{domain}-HostedZoneId` |
| `HostedZoneName` | Hosted Zone name | `{domain}-HostedZoneName` |
| `NameServers` | Authoritative nameservers | — |
| `RegistrationStatus` | Domain registration status | — |

## Prerequisites and Requirements

### AWS Account Requirements

- AWS account with appropriate permissions for:
  - Route 53 (domain registration requires us-east-1 region)
  - CloudTrail and S3 management
  - CloudWatch Logs
  - IAM role creation
  - Lambda function deployment

### Account Configuration

Before deployment, ensure AWS Account settings are populated:

```text
AWS Console → Billing → Account Settings
```

Required fields:

- Full Name
- Address Line 1
- City
- State/Region
- Country Code
- Postal Code
- Phone Number

Alternatively, configure billing contact:

```text
AWS Console → Billing → Billing Preferences → Billing Alerts Contact
Information
```

### Software Requirements

- Python 3.8 or higher
- AWS CDK CLI (v2.x)
- AWS CLI configured with appropriate credentials
- Boto3 SDK (included with AWS CDK)

### Installation

```bash
# Install AWS CDK (if not already installed)
npm install -g aws-cdk

# Verify CDK installation
cdk --version

# Install Python dependencies
pip install -r requirements.txt
```

## Usage Instructions

### Deployment

1. **Configure the domain name** in your CDK app or environment:

```python
config = {
    "domain_name": "example.com"
}

stack = DomainStack(app, "DomainStack", config=config)
```

1. **Synthesize the CloudFormation template**:

```bash
cdk synth
```

1. **Preview changes** (optional):

```bash
cdk diff
```

1. **Deploy the stack**:

```bash
cdk deploy
```

1. **Confirm the deployment prompt** when prompted for resource creation.

### Post-Deployment

After successful deployment:

1. **Verify domain registration** in AWS Console:
   - Route 53 → Registered Domains → Check status

2. **Update domain contacts** (if necessary):
   - Route 53 → Registered Domains → [Domain] → Registrant Details

3. **Update nameservers** at your domain registrar (if transferring from
external registrar)

4. **Monitor CloudTrail logs**:
   - CloudTrail Console → Event History
   - CloudWatch Logs → Log Groups → `/aws/cloudtrail/DomainCloudTrail`

### Cleanup

To remove the infrastructure:

```bash
cdk destroy
```

**Note**: The access log bucket is retained by default. To also delete it:

```bash
# Manually delete the access log bucket in S3 console, then run:
cdk destroy
```

## Architecture Explanation

### CloudTrail Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    AWS Account Events                    │
│  (Multi-Region: Management Events, Global Services)     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐         ┌──────▼──────┐
    │ CloudTrail│         │ CloudTrail  │
    │  Bucket   │         │ Log Group   │
    │  (S3)     │         │ (CloudWatch)│
    │           │         │             │
    └────┬──────┘         └─────────────┘
         │
    ┌────▼──────────┐
    │  Access Logs  │
    │    Bucket     │
    │   (Glacier)   │
    └───────────────┘
```

**Data Flow**:

1. AWS API calls across all regions are captured
2. Events are simultaneously logged to:
   - S3 bucket (primary audit trail)
   - CloudWatch Logs (real-time monitoring)
3. S3 access logs track all bucket operations
4. Lifecycle policies automatically archive and expire logs

### Domain Registration Workflow

```text
┌──────────────────────────────────────────────────────┐
│            Custom Resource Invocation                │
│          (CloudFormation Stack Creation)             │
└──────────────────┬───────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Lambda Handler     │
        │   Invocation        │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Check if Domain Exists     │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   Yes  │                     │  No
    ┌───▼────┐          ┌────▼──────┐
    │ Reuse  │          │ Check     │
    │ Zone   │          │ Available │
    └────────┘          └────┬──────┘
        │                    │
        │              ┌─────┴────┐
        │              │          │
        │         Available   Not Available
        │         (Register)  (Fail)
        │              │
        │         ┌────▼──────────────┐
        │         │ Get Contact Info  │
        │         │ (Account/Org APIs)│
        │         └────┬──────────────┘
        │              │
        │         ┌────▼──────────┐
        │         │ Register Domain│
        │         └────┬──────────┘
        │              │
        │         ┌────▼──────────────────┐
        │         │ Wait for Hosted Zone  │
        │         │ (Exponential Backoff) │
        │         └────┬──────────────────┘
        │              │
        └──────────┬───┘
                   │
        ┌──────────▼──────────────┐
        │ Return Hosted Zone ID   │
        │ & Nameservers           │
        └──────────┬──────────────┘
                   │
        ┌──────────▼──────────────┐
        │ Stack Creation Complete │
        └─────────────────────────┘
```

### Custom Resource Lifecycle

1. **Stack Create**: Lambda handler registers domain or reuses existing
2. **Stack Update**: Lambda handler updates domain configuration
(if properties change)
3. **Stack Delete**: Lambda handler completes successfully
(no domain deletion)

**Retry Logic**:

- Hosted zone creation uses exponential backoff: 1s, 2s, 4s, 8s... up to
14 minutes
- Domain registration can take 5-30 minutes; stack may need redeployment

## Configuration Details

### Domain Configuration

Configuration is passed to the stack via dictionary:

```python
config = {
    "domain_name": "mycompany.com"
}
```

Supported TLDs: All Route 53 supported domains (.com, .org, .net, .co.uk,
etc.)

### Contact Information Retrieval

The Lambda function retrieves registrant contact information in this
priority order:

1. **Organization email** (if AWS Organization member)
2. **Billing alternate contact email** (if configured)
3. **Generated email** (falls back to admin@{company}.com with warning)

**Phone Number Formatting**:

- Automatically detects country from AWS account
- Strips non-digit characters
- Prepends country dialing code (24 supported countries)
- Format: `+{code}.{number}`

### S3 Bucket Policies

The CloudTrail bucket automatically receives a policy allowing CloudTrail
service access:

```json
{
  "Action": "s3:PutObject",
  "Principal": {"Service": "cloudtrail.amazonaws.com"},
  "Resource": "arn:aws:s3:::bucket-name/prefix/*",
  "Condition": {
    "StringEquals": {
      "s3:x-amz-acl": "bucket-owner-full-control"
    }
  }
}
```

### Encryption Configuration

- **S3 Buckets**: S3-managed SSE-S3 encryption
- **CloudTrail**: File integrity validation enabled
- **Transport**: SSL/TLS enforcement on all buckets

## Testing Approach

### Unit Testing

Test stack instantiation:

```python
from aws_cdk import assertions as assertions
from stack import DomainStack

def test_stack_creates_buckets():
    config = {"domain_name": "test.com"}
    template = assertions.Template.from_stack(DomainStack(None, "test",
                                                           config))

    template.resource_count_is("AWS::S3::Bucket", 2)
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {"Status": "Suspended"}
    })
```

### Integration Testing

1. **Pre-deployment**:
   - Verify AWS account has required contact information
   - Confirm domain availability using Route 53 console

1. **Post-deployment**:

```bash
# Verify CloudTrail is logging
aws cloudtrail describe-trails

# Check S3 buckets
aws s3 ls | grep cloudtrail

# Verify hosted zone
aws route53 list-hosted-zones-by-name --dns-name example.com

# Check Lambda execution
aws logs tail /aws/lambda/DomainRegistrationHandler --follow
```

1. **CloudTrail validation**:
   - Event appears in CloudTrail within 15 minutes
   - CloudWatch Logs show real-time entries

### Domain Registration Testing

To test without deploying:

```python
import boto3

route53domains = boto3.client('route53domains', region_name='us-east-1')

# Check domain availability
response = route53domains.check_domain_availability(
    DomainName='test-domain.com')
print(response['Availability'])  # AVAILABLE, UNAVAILABLE, etc.
```

## Security Considerations

### CloudTrail Security

- ✅ **Multi-region coverage**: Captures events from all regions
- ✅ **Global service events**: Includes IAM, CloudFront, Route 53
- ✅ **File validation**: Cryptographic signature verification enabled
- ✅ **Access logging**: All S3 bucket operations are logged
- ✅ **Encryption in transit**: SSL/TLS enforced
- ✅ **Encryption at rest**: S3-managed encryption enabled

### S3 Security

- ✅ **Block public access**: All public access disabled
- ✅ **Versioning disabled**: Simplified compliance (logs are immutable)
- ✅ **Enforced SSL**: Deny unencrypted connections
- ✅ **Lifecycle archival**: Cost-effective long-term retention
- ✅ **Access logging**: Separate bucket for audit trail operations

### Lambda Security

- ✅ **Least privilege IAM**: Only required Route 53/Account API
permissions
- ✅ **Timeout protection**: 15-minute timeout prevents hanging
- ✅ **Error handling**: Sensitive data not logged in traces
- ✅ **No hardcoded credentials**: Uses IAM role assumption

### Domain Registration Security

- ✅ **Privacy protection**: All domain contacts protected
- ✅ **Contact validation**: AWS Account API provides verified contact
info
- ✅ **Registrant contact**: Matches organization details
- ✅ **WHOIS privacy**: Enabled by default

### IAM Permissions

Minimal IAM policy for Lambda execution:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53domains:CheckDomainAvailability",
        "route53domains:GetDomainDetail",
        "route53domains:GetOperationDetail",
        "route53domains:RegisterDomain",
        "route53:ListHostedZonesByName",
        "route53:GetHostedZone",
        "route53:CreateHostedZone",
        "account:GetContactInformation",
        "account:GetAlternateContact",
        "organizations:DescribeOrganization"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### Domain Registration Failures

#### "Domain not available"

```text
Solution: Try alternative domain name
- Check availability: Route 53 Console → Domains → Check Domain
Availability
- Use different TLD (.co, .io, .dev)
```

#### "Missing AWS Account Contact Information"

```text
Error: AWS account missing contact fields...

Solution: Update AWS account settings
1. AWS Console → Billing → Account
2. Fill in all required fields:
   - Full Name
   - Street Address
   - City
   - State/Province
   - Postal Code
   - Phone Number
3. Re-deploy: cdk deploy
```

#### "Invalid Phone Number"

```text
Solution: Update AWS Account phone number
- Use format: +1-555-0123 or +44-201-555-0123
- Supported countries: 24 (see COUNTRY_DIALING_CODES in handler.py)
- Ensure country code matches CountryCode setting
```

#### "Hosted Zone Not Created"

```text
Message: Hosted zone not created within timeout period

Cause: AWS can take 5-30 minutes to create hosted zone
Solution:
1. Wait 5-10 minutes
2. Re-run: cdk deploy
3. Check: Route 53 → Hosted Zones
4. Verify: Domain status in Route 53 → Domains
```

### CloudTrail Issues

#### "No events appearing in CloudWatch Logs"

```text
Solution: Check Lambda logs
1. CloudWatch Logs → /aws/cloudtrail/DomainCloudTrail
2. Verify retention period: 1 year
3. Check S3 bucket for events:
   aws s3 ls s3://cloudtrail-bucket-name/
```

#### "S3 access denied errors"

```text
Solution: Verify CloudTrail bucket policy
1. S3 → [CloudTrail Bucket] → Permissions → Bucket Policy
2. Should allow: cloudtrail.amazonaws.com PutObject
3. Re-deploy: cdk deploy (auto-corrects policy)
```

#### "Lifecycle transition failures"

```text
Solution: Verify Glacier supported regions
- Glacier available in most regions
- Check S3 → [Bucket] → Management → Lifecycle Rules
- Ensure rule transitions are valid
```

### Custom Resource Issues

#### "Lambda timeout (900 seconds)"

```text
Cause: Domain registration or hosted zone creation took too long
Solution:
1. Check Lambda logs: CloudWatch → /aws/lambda/DomainRegistrationHandler
2. Manual verification: Route 53 → Domains & Hosted Zones
3. If successful, run: cdk destroy && cdk deploy
```

#### "Custom resource creation failed"

```text
Solution: Check Lambda logs
1. CloudWatch Logs → /aws/lambda/DomainRegistrationHandler
2. Look for error messages (contact info missing, API failures)
3. Fix issues and re-deploy
4. Check CloudFormation Events for details
```

### CloudFormation Stack Issues

#### "Delete failed - Access denied to access log bucket"

```text
Solution: Manually delete access log bucket
1. S3 Console → Find "cloudtrailaccesslogbucket" bucket
2. Empty bucket: Select all → Delete
3. Delete bucket: Bucket menu → Delete Bucket
4. Re-run: cdk destroy
```

#### "Cannot update stack - hosted zone already exists"

```text
Solution: Use Hosted Zone ID from previous deployment
- Custom resource returns existing hosted zone
- No conflicts if re-deploying same domain
- Cannot change domain name without destroying stack
```

### Debugging Commands

```bash
# View stack outputs
aws cloudformation describe-stacks --stack-name DomainStack \
  --query 'Stacks[0].Outputs'

# Check CloudTrail status
aws cloudtrail describe-trails --trail-name-list DomainCloudTrail

# Monitor Lambda execution
aws logs tail /aws/lambda/DomainRegistrationHandler --follow

# Verify hosted zone
aws route53 list-hosted-zones-by-name --dns-name example.com

# Check domain registration
aws route53domains get-domain-detail --domain-name example.com \
  --region us-east-1

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name DomainStack \
  --query 'StackEvents[*].[Timestamp,LogicalResourceId,ResourceStatus]'
```

### Enabling Debug Logging

In Lambda handler, add debug output:

```python
import json

# At handler start:
print("Event:", json.dumps(event, indent=2))
print("Environment:", os.environ)

# In functions:
print(f"DEBUG: {variable_name} = {variable_value}")
```

Re-deploy and check CloudWatch Logs for detailed output.

---

**Last Updated**: 2024
**Version**: 1.0
**License**: MIT (or your project license)
**Support**: Check AWS CDK documentation and Route 53 API reference
