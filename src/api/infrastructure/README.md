# 10U Labs API Infrastructure

This AWS CDK project deploys a comprehensive API infrastructure for 10ulabs.com,
including API Gateway, Lambda functions, CloudFront distribution, and GitHub
self-hosted runner environments using both ECS Fargate and EC2 instances.

## Overview

The infrastructure creates a production-ready API platform with:

- RESTful API endpoints served through AWS API Gateway
- Lambda functions for health checks, echo testing, and catch-all routing
- CloudFront distribution for global content delivery
- S3-hosted documentation with automatic deployment
- ECS Fargate and EC2-based GitHub self-hosted runners
- Comprehensive security with WAF, VPC, and IAM roles
- SSL/TLS certificates and custom domain configuration

## Purpose and Key Features

### Core API Platform

- **API Gateway**: RESTful API with OpenAPI specification
- **Lambda Functions**: Serverless compute for API endpoints
- **CloudFront**: Global CDN with caching and SSL termination
- **Route 53**: DNS management for custom domain

### GitHub Runner Infrastructure

- **ECS Fargate Runners**: Ephemeral containerized CI/CD runners
- **EC2 Spot Runners**: Cost-effective compute for larger workloads
- **ECR Repository**: Container image storage with lifecycle policies
- **VPC Network**: Isolated networking environment

### Security and Monitoring

- **AWS WAF**: Web application firewall protection
- **Secrets Manager**: Secure credential storage
- **CloudWatch Logs**: Centralized logging and monitoring
- **IAM Roles**: Least-privilege access controls

## Resources Created

### Networking and Compute

- **VPC**: Custom VPC with public subnets across multiple AZs
- **ECS Cluster**: Container orchestration for GitHub runners
- **Security Groups**: Network access controls for runner tasks
- **ECR Repository**: Docker image registry with automatic cleanup

### API Infrastructure

- **API Gateway REST API**: RESTful endpoints with OpenAPI spec
- **Lambda Functions**: Health, echo, and catch-all handlers
- **CloudFront Distribution**: CDN with multiple origin behaviors
- **S3 Bucket**: Static documentation hosting

### Security and Secrets

- **ACM Certificate**: SSL/TLS certificate for custom domain
- **WAF Web ACL**: Application-layer security rules
- **Secrets Manager**: GitHub tokens and webhook secrets
- **IAM Roles**: Service roles for Lambda, ECS, and EC2

### DNS and Monitoring

- **Route 53 Records**: DNS alias records for custom domain
- **CloudWatch Log Groups**: Centralized logging infrastructure
- **Custom Resources**: CloudFront cache invalidation automation

## Prerequisites and Requirements

### Python Dependencies

Install the required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Required Packages

- **aws-cdk-lib==2.150.0**: AWS CDK framework
- **constructs>=10.0.0,<11.0.0**: CDK constructs library
- **boto3>=1.34.0**: AWS SDK for Python
- **boto3-stubs[route53,route53domains,account,organizations]>=1.34.0**: 
  Type hints for boto3
- **requests>=2.31.0**: HTTP library for API calls
- **types-requests>=2.31.0**: Type hints for requests
- **pyyaml>=6.0.1**: YAML processing for OpenAPI spec
- **types-pyyaml>=6.0.12**: Type hints for PyYAML

### System Dependencies

- **Python 3.11+**: Required runtime for CDK and Lambda functions
- **Node.js 18+**: Required for AWS CDK CLI installation
- **Git**: Required for repository management

### AWS Setup

- Valid AWS account with appropriate permissions
- AWS credentials configured (via AWS credentials file, environment
  variables, or IAM roles)
- Route 53 hosted zone for parent domain (must export HostedZoneId)

## Configuration

### Main Configuration (`config.json`)

The infrastructure uses a comprehensive configuration file:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 99,
      "nat_gateways": 0
    }
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  },
  "github": {
    "org": "10U-Labs-LLC",
    "repo": "10U-Labs-LLC/10ulabs.com"
  }
}
```

### CDK Configuration (`cdk.json`)

CDK-specific settings including feature flags and watch mode:

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__"]
  }
}
```

### Required Secrets

Before deployment, create these secrets in AWS Secrets Manager:

- **github-runner/credentials**: GitHub personal access token
- **api-webhook-secret**: Auto-generated webhook verification secret

## Usage Instructions

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI:**

   ```bash
   npm install -g aws-cdk@2.150.0
   ```

4. **Configure AWS credentials:**

   ```bash
   # Via AWS credentials file, environment variables, or IAM roles
   export AWS_PROFILE=your-profile
   export AWS_REGION=us-east-1
   ```

### Deployment

1. **Bootstrap CDK (first time only):**

   ```bash
   cdk bootstrap aws://781581267945/us-east-1
   ```

2. **Review the changes:**

   ```bash
   cdk diff
   ```

3. **Deploy the infrastructure:**

   ```bash
   cdk deploy TenULabsApi
   ```

4. **Verify deployment:**

   ```bash
   curl https://api.10ulabs.com/health
   ```

### Development Workflow

1. **Watch mode for iterative development:**

   ```bash
   cdk watch
   ```

2. **Update README documentation:**

   ```bash
   python scripts/readme.py --update --project-dir . --aws-region us-east-1
   ```

3. **Check README currency:**

   ```bash
   python scripts/readme.py --check --project-dir . --aws-region us-east-1
   ```

### Using Deployed Resources

#### API Endpoints

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Service**: `POST https://api.10ulabs.com/v1/echo`
- **API Documentation**: `https://api.10ulabs.com/`
- **OpenAPI Spec**: `https://api.10ulabs.com/openapi.yaml`

#### GitHub Runners

- **Fargate Runners**: Automatically triggered by webhook events
- **EC2 Spot Runners**: Cost-effective for longer workflows
- **Container Registry**: Available at ECR repository URI

## Architecture Overview

### Component Interactions

1. **CloudFront Distribution** receives all requests to api.10ulabs.com
2. **S3 Origin** serves static documentation (/, /openapi.yaml, /404.html)
3. **API Gateway Origin** handles API endpoints (/health, /v1/*)
4. **Lambda Functions** process API requests and return responses
5. **Route 53** provides DNS resolution for the custom domain

### Authentication and Authorization Flows

#### API Access

- Public API endpoints with no authentication required
- WAF provides application-layer protection
- CloudFront adds geographic and DDoS protection

#### GitHub Runner Authentication

- **Fargate Tasks**: Use IAM task roles with Secrets Manager access
- **EC2 Instances**: Use instance profiles with ECR and termination 
  permissions
- **GitHub Tokens**: Stored securely in AWS Secrets Manager

### Data Flows

1. **API Requests**: Client → CloudFront → API Gateway → Lambda → Response
2. **Documentation**: Client → CloudFront → S3 → Static Content
3. **Runner Deployment**: Webhook → Lambda → ECS/EC2 → GitHub Registration
4. **Container Images**: GitHub Actions → ECR → ECS Fargate Tasks

### Integration Points

- **GitHub Webhooks**: Trigger runner provisioning via API Gateway
- **ECR Integration**: Automatic image pulls for Fargate tasks
- **Secrets Manager**: Centralized credential management
- **CloudWatch**: Unified logging and monitoring

## Security Considerations

### Network Security

- **VPC Isolation**: Runners operate in dedicated VPC with public subnets
- **Security Groups**: Restrictive ingress rules, allow outbound for updates
- **No NAT Gateway**: Cost optimization with direct internet access

### Access Controls

- **IAM Roles**: Least-privilege principles for all services
- **Secrets Manager**: Encrypted storage for sensitive credentials
- **Resource-Based Policies**: Fine-grained access to AWS services

### Application Security

- **WAF Protection**: Application-layer filtering and rate limiting
- **SSL/TLS Encryption**: End-to-end encryption via ACM certificates
- **Webhook Verification**: HMAC signature validation for GitHub events

### Operational Security

- **Log Retention**: One week for API logs, one month for access logs
- **Image Scanning**: ECR vulnerability scanning on push
- **Automatic Cleanup**: ECR lifecycle rules and S3 object deletion

## Troubleshooting

### Common Deployment Issues

**CDK Bootstrap Required:**

```bash
# Error: Need to perform AWS CDK bootstrap
cdk bootstrap aws://ACCOUNT_ID/REGION
```

**Certificate Validation Timeout:**

- Verify Route 53 hosted zone exists and is accessible
- Check DNS propagation with `dig` or `nslookup`
- Ensure parent domain exports HostedZoneId correctly

**Lambda Permission Errors:**

```bash
# Check CloudWatch logs for specific permission issues
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
```

### Runtime Issues

**API Gateway 500 Errors:**

- Check Lambda function logs in CloudWatch
- Verify Lambda function permissions for API Gateway
- Test Lambda functions individually in AWS Console

**CloudFront Cache Issues:**

- Create manual invalidation for updated content:

   ```bash
   aws cloudfront create-invalidation \
     --distribution-id DISTRIBUTION_ID \
     --paths "/*"
   ```

**ECS Task Failures:**

- Check ECS service logs in CloudWatch
- Verify ECR repository contains valid runner images
- Check IAM task role permissions for Secrets Manager

### Debugging Commands

**View CDK context and cached values:**

```bash
cdk context --clear  # Clear cached context
cdk ls              # List all stacks
cdk diff            # Show pending changes
```

**Check AWS resource status:**

```bash
# API Gateway
aws apigateway get-rest-apis --query 'items[?name==`TenULabsApi`]'

# ECS Cluster
aws ecs describe-clusters --clusters TenULabsRunnerCluster

# Route 53 Records
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID
```
