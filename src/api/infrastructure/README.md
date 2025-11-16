# TenU Labs API Infrastructure

Comprehensive AWS CDK infrastructure for deploying the api.10ulabs.com API
Gateway with Lambda functions, CloudFront distribution for documentation,
and self-hosted GitHub runner environments for CI/CD.

## Overview

This infrastructure creates a production-ready API platform that combines:

- **API Gateway** with Lambda functions for REST endpoints
- **CloudFront CDN** for global content delivery and documentation hosting
- **Self-hosted GitHub runners** on both Fargate and EC2 for CI/CD
- **Custom domain** with SSL certificates and DNS management
- **Security features** including WAF protection and VPC isolation

The infrastructure supports the 10U Labs API ecosystem with automatic
scaling, comprehensive monitoring, and secure deployment pipelines.

## Key Features

- Multi-origin CloudFront distribution (API Gateway + S3 documentation)
- Self-hosted GitHub runners with spot instance support
- Automated certificate management with Route53 validation
- WAF protection for API endpoints
- ECS Fargate tasks for containerized workloads
- EC2 spot instances with auto-termination for cost optimization
- Comprehensive IAM security with least-privilege access
- Integrated secrets management for GitHub tokens and webhooks

## Resources Created

### Networking & Security

- **VPC** with public subnets and configurable availability zones
- **Security Groups** for runner isolation and controlled access
- **WAF Web ACL** with CloudFront integration for DDoS protection
- **Secrets Manager** entries for GitHub tokens and webhook secrets

### Compute & Containers

- **ECS Cluster** for orchestrating Fargate runner tasks
- **ECR Repository** with lifecycle policies for runner images
- **Fargate Task Definition** with GitHub integration environment
- **EC2 IAM Roles** and instance profiles for spot runners

### API & Content Delivery

- **API Gateway REST API** with OpenAPI specification integration
- **Lambda Functions** for health, echo, and catch-all endpoints
- **CloudFront Distribution** with multiple behavior patterns
- **S3 Bucket** for API documentation and static assets

### DNS & Certificates

- **ACM Certificate** with automatic DNS validation
- **Route53 A Record** for custom domain mapping
- **CloudFront Function** for URL rewriting and routing

### Monitoring & Logging

- **CloudWatch Log Groups** for API Gateway access logs
- **Lambda function logs** with configurable retention
- **ECS task logging** with centralized log collection

## Prerequisites

### System Dependencies

- **Python 3.11+** for running AWS CDK applications
- **Node.js 18+** required by AWS CDK framework
- **Git** for repository management and version control

### Python Dependencies

Install the required packages from requirements.txt:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0` - AWS CDK framework
- `constructs>=10.0.0,<11.0.0` - CDK construct library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`
- `requests>=2.31.0` - HTTP client library
- `types-requests>=2.31.0` - Type stubs for requests
- `pyyaml>=6.0.1` - YAML parser for OpenAPI specs
- `types-pyyaml>=6.0.12` - Type stubs for PyYAML

### AWS Prerequisites

- Valid AWS account with appropriate permissions
- Existing Route53 hosted zone for the parent domain
- GitHub personal access token stored in AWS Secrets Manager
- AWS credentials configured (via AWS SSO, environment, or profiles)

## Configuration

### Primary Configuration (config.json)

The main configuration file defines all infrastructure parameters:

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
      "nat_gateways": 0,
      "subnet_configuration": {
        "public_subnet_cidr_mask": 24
      }
    }
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  }
}
```

### CDK Configuration (cdk.json)

CDK-specific settings and feature flags:

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

### Required Secrets

1. **GitHub Token Secret** (`github-runner/credentials`)

   ```bash
   aws secretsmanager create-secret \
     --name "github-runner/credentials" \
     --description "GitHub personal access token for runners" \
     --secret-string "your_github_token"
   ```

2. **Webhook Secret** (automatically generated during deployment)

## Installation & Deployment

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install CDK (if not already installed)
npm install -g aws-cdk
```

### 2. Configure AWS Credentials

```bash
# Using AWS SSO (recommended)
aws sso login --profile your-profile

# Or export credentials
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
```

### 3. Bootstrap CDK (first-time only)

```bash
cdk bootstrap aws://781581267945/us-east-1
```

### 4. Deploy Infrastructure

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy with confirmation
cdk deploy --require-approval never

# Deploy with specific profile
cdk deploy --profile your-profile
```

### 5. Verify Deployment

```bash
# Test API health endpoint
curl https://api.10ulabs.com/health

# Test echo endpoint
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

## Usage Instructions

### API Endpoints

The deployed API provides several endpoints:

- `GET /health` - Health check endpoint
- `POST /v1/echo` - Echo service for testing
- `GET /` - API documentation (served from S3)
- `GET /openapi.yaml` - OpenAPI specification

### GitHub Runner Management

#### Fargate Runners

Fargate runners automatically scale based on GitHub webhook events:

- **Labels**: `ephemeral-ecs-fargate-spot`
- **Resources**: 256 CPU units, 512 MB memory
- **Lifecycle**: Ephemeral (terminate after single job)

#### EC2 Spot Runners

EC2 runners provide cost-effective compute for longer workflows:

- **Instance Types**: t4g.large, t4g.medium, t4g.small
- **Labels**: `ephemeral-ec2-spot-instance`
- **Max Price**: $0.05 per hour
- **Auto-termination**: Self-terminate after job completion

### Documentation Updates

Static documentation is automatically deployed from the repository:

1. Update `index.html` or `openapi.yaml` files
2. Redeploy stack to sync changes to S3
3. CloudFront automatically invalidates cached content

## Architecture Overview

### Multi-Origin CloudFront Distribution

The architecture uses CloudFront with two origins:

```
┌─────────────────┐    ┌──────────────────┐
│   CloudFront    │────│   API Gateway    │
│  Distribution   │    │    (API calls)   │
│                 │    └──────────────────┘
│                 │    ┌──────────────────┐
│                 │────│   S3 Bucket      │
└─────────────────┘    │ (Documentation)  │
                       └──────────────────┘
```

### Request Routing

CloudFront routes requests based on path patterns:

- `/` → S3 (documentation home page)
- `/openapi.yaml` → S3 (API specification)
- `/health` → API Gateway (health endpoint)
- `/v1/*` → API Gateway (versioned API endpoints)
- `/*` → API Gateway (catch-all for undefined routes)

### GitHub Runner Architecture

```
┌──────────────────┐    ┌─────────────────┐
│  GitHub Webhook  │────│  Lambda Handler │
└──────────────────┘    └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   ECS Cluster   │
                        │ ┌─────────────┐ │
                        │ │   Fargate   │ │
                        │ │    Tasks    │ │
                        │ └─────────────┘ │
                        └─────────────────┘
```

### Security Flow

1. **WAF Protection**: All requests pass through WAF rules
2. **TLS Termination**: CloudFront handles SSL/TLS encryption
3. **API Authentication**: Lambda functions validate requests
4. **Runner Isolation**: VPC security groups control access
5. **Secrets Management**: GitHub tokens stored in Secrets Manager

## Security Considerations

### Network Security

- **VPC Isolation**: Runners operate in dedicated subnets
- **Security Groups**: Restrictive ingress/egress rules
- **Public Subnets Only**: No NAT gateways to reduce attack surface

### IAM Security

- **Least Privilege**: Minimal permissions for each role
- **Resource-Specific**: Policies scoped to specific resources
- **Condition-Based**: Additional conditions for sensitive operations

### Data Protection

- **Encryption in Transit**: TLS 1.2+ for all API communication
- **Encryption at Rest**: S3 and Secrets Manager use AWS-managed keys
- **Secrets Rotation**: Automated rotation for webhook secrets

### Runner Security

- **Ephemeral Instances**: Runners terminate after each job
- **Spot Instances**: Reduced cost with automatic termination
- **Self-Termination**: EC2 instances can only terminate themselves

## Troubleshooting

### Common Deployment Issues

#### CDK Bootstrap Errors

```bash
# Error: Need to perform AWS CDK bootstrap
cdk bootstrap aws://ACCOUNT-ID/REGION

# Error: Invalid credentials
aws sts get-caller-identity  # Verify AWS access
```

#### Domain Validation Failures

```bash
# Check Route53 hosted zone exists
aws route53 list-hosted-zones --query 'HostedZones[?Name==`10ulabs.com.`]'

# Verify certificate status
aws acm list-certificates --region us-east-1
```

### Runtime Issues

#### API Gateway 502 Errors

1. Check Lambda function logs in CloudWatch
2. Verify Lambda permissions for API Gateway invocation
3. Test Lambda function directly in AWS Console

#### CloudFront Distribution Issues

```bash
# Create invalidation for updated content
aws cloudfront create-invalidation \
  --distribution-id E1234EXAMPLE \
  --paths "/*"
```

#### Runner Connection Problems

1. Verify GitHub token in Secrets Manager
2. Check ECS task logs for container startup issues
3. Ensure ECR repository contains runner image

### Monitoring Commands

```bash
# View API Gateway logs
aws logs describe-log-streams \
  --log-group-name /aws/apigateway/TenULabsApi

# Check Lambda function metrics
aws logs filter-log-events \
  --log-group-name /aws/lambda/HealthHandler \
  --start-time $(date -d '1 hour ago' +%s)000

# Monitor ECS task status
aws ecs list-tasks --cluster TenULabsRunnerCluster
```

### Performance Optimization

- **CloudFront Caching**: Adjust cache policies for static content
- **Lambda Memory**: Increase memory for faster cold starts
- **API Gateway Throttling**: Configure usage plans for rate limiting
- **Spot Instance Types**: Adjust instance types based on workload needs
