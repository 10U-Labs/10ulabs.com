# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure stack that deploys a fully-featured
API platform with CloudFront distribution, Lambda functions, and GitHub
self-hosted runner capabilities for api.10ulabs.com.

## Overview

This infrastructure creates a production-ready API platform combining:

- **API Gateway** with Lambda-backed endpoints and OpenAPI specification
- **CloudFront Distribution** serving both API and documentation content
- **GitHub Self-Hosted Runners** on AWS Fargate and EC2 for CI/CD
- **S3-hosted Documentation** with automated deployment
- **WAF Protection** and SSL/TLS termination
- **Route53 DNS** management with custom domain configuration

## Key Features

- **Hybrid Content Delivery**: API endpoints and static documentation served
  through a single CloudFront distribution
- **Multi-Runtime Runners**: Support for both Fargate and EC2-based GitHub
  self-hosted runners with spot instance optimization
- **Automated Certificate Management**: SSL certificates provisioned and
  validated through AWS Certificate Manager
- **Security-First Design**: WAF protection, VPC isolation, and IAM
  least-privilege access
- **Infrastructure as Code**: Complete AWS CDK implementation with
  configuration-driven deployment

## Resources Created

### Core Infrastructure

- **VPC**: Isolated network with public subnets across multiple AZs
- **Route53**: DNS records and hosted zone integration
- **Certificate Manager**: SSL certificate for api.10ulabs.com
- **CloudFront**: Global CDN with custom domain and WAF integration

### API Platform

- **API Gateway**: REST API with OpenAPI specification
- **Lambda Functions**: Health check, echo endpoint, and catch-all handlers
- **S3 Bucket**: Documentation hosting with automated content deployment
- **CloudWatch Logs**: API access logs and Lambda function monitoring

### GitHub Runner Infrastructure

- **ECS Cluster**: Container orchestration for Fargate runners
- **ECR Repository**: Docker image storage for runner containers
- **Fargate Task Definition**: Ephemeral runner configuration
- **EC2 IAM Roles**: Instance profiles for EC2-based runners
- **Security Groups**: Network access control for runner instances

### Security & Secrets

- **WAF Web ACL**: Application-level protection for CloudFront
- **Secrets Manager**: GitHub tokens and webhook secrets storage
- **IAM Roles**: Service-specific permissions for all components

## Prerequisites

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages from `requirements.txt`:

- `aws-cdk-lib==2.150.0` - AWS CDK core library
- `constructs>=10.0.0,<11.0.0` - CDK constructs framework
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` -
  Type hints for boto3
- `requests>=2.31.0` - HTTP library for API calls
- `types-requests>=2.31.0` - Type hints for requests
- `pyyaml>=6.0.1` - YAML processing for OpenAPI specs
- `types-pyyaml>=6.0.12` - Type hints for PyYAML

### System Dependencies

- **Node.js** (v18 or later) - Required for AWS CDK CLI
- **Python** (3.11 or later) - Runtime for CDK application
- **Git** - Version control and repository access

### AWS Prerequisites

- AWS account with appropriate permissions
- Route53 hosted zone for parent domain (10ulabs.com)
- GitHub token stored in AWS Secrets Manager
- CDK bootstrap completed in target region

## Configuration

### config.json Structure

The infrastructure is configured through `config.json`:

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

### CDK Configuration

The `cdk.json` file configures CDK behavior:

- **App Entry Point**: `python3 app.py`
- **Watch Mode**: Automatic redeployment on file changes
- **Feature Flags**: Modern CDK feature enablement

## Usage

### Installation

1. Clone the repository and navigate to the infrastructure directory

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK CLI:

   ```bash
   npm install -g aws-cdk
   ```

4. Bootstrap CDK in your AWS account:

   ```bash
   cdk bootstrap
   ```

### Deployment

1. Configure AWS credentials for your target account

2. Review and customize `config.json` for your environment

3. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

4. Confirm deployment when prompted

### Using the Deployed Resources

#### API Endpoints

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Service**: `POST https://api.10ulabs.com/v1/echo`
- **Documentation**: `https://api.10ulabs.com/` (S3-hosted content)
- **OpenAPI Spec**: `https://api.10ulabs.com/openapi.yaml`

#### GitHub Runners

The infrastructure supports two types of self-hosted runners:

1. **Fargate Runners**: Containerized, fully managed
   - Labels: `ephemeral-ecs-fargate-spot`
   - Automatic scaling and cleanup

2. **EC2 Runners**: Virtual machine-based with spot instances
   - Labels: `ephemeral-ec2-spot-instance`
   - Cost-optimized with multiple instance types

## Architecture Overview

### Request Flow

1. **DNS Resolution**: Route53 resolves api.10ulabs.com to CloudFront
2. **CDN Routing**: CloudFront routes requests based on path patterns:
   - `/health`, `/v1/*` → API Gateway → Lambda functions
   - `/`, `/openapi.yaml` → S3 bucket (documentation)
3. **API Processing**: Lambda functions handle business logic
4. **Response Delivery**: CloudFront caches and delivers responses globally

### Runner Orchestration

1. **GitHub Webhook**: Triggers runner provisioning on workflow events
2. **ECS Tasks**: Fargate runners start automatically for containerized jobs
3. **EC2 Instances**: Spot instances launch for longer-running or
   specialized workloads
4. **Self-Termination**: Ephemeral runners clean up after job completion

### Security Architecture

- **WAF Protection**: Application-layer filtering at CloudFront edge
- **VPC Isolation**: Runners operate in dedicated network segments
- **IAM Boundaries**: Service-specific roles with minimal permissions
- **Secrets Management**: Centralized credential storage and rotation

## Security Considerations

### Network Security

- **Public Subnets Only**: Cost-optimized design without NAT gateways
- **Security Groups**: Restrictive ingress rules for runner instances
- **VPC Flow Logs**: Network traffic monitoring (optional)

### Access Control

- **IAM Roles**: Separate roles for API, runners, and deployment
- **Resource Policies**: S3 bucket and ECR repository access restrictions
- **Secrets Rotation**: Automated GitHub token and webhook secret rotation

### Data Protection

- **TLS Encryption**: End-to-end encryption for all API traffic
- **S3 Encryption**: Server-side encryption for documentation storage
- **CloudWatch Logs**: Centralized logging with retention policies

## Troubleshooting

### Common Issues

#### CDK Deployment Failures

```bash
# Check CDK version compatibility
cdk --version

# Validate CloudFormation template
cdk synth

# Force stack diff to identify changes
cdk diff
```

#### SSL Certificate Validation

If certificate validation fails:

1. Verify Route53 hosted zone delegation
2. Check DNS propagation: `dig api.10ulabs.com`
3. Review Certificate Manager validation records

#### Lambda Function Errors

Check CloudWatch Logs for function-specific issues:

```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
```

#### Runner Connection Issues

Verify runner connectivity:

1. Check ECS task logs in CloudWatch
2. Validate GitHub token permissions in Secrets Manager
3. Review security group rules for outbound HTTPS access

### Monitoring

Key CloudWatch metrics to monitor:

- **API Gateway**: Request count, latency, error rates
- **Lambda**: Duration, error count, concurrent executions
- **CloudFront**: Cache hit ratio, origin response time
- **ECS**: Task count, CPU/memory utilization

### Support

For infrastructure issues:

1. Check CloudFormation stack events for deployment errors
2. Review CloudWatch Logs for runtime issues
3. Validate configuration against `config.json` schema
4. Ensure AWS service limits are not exceeded
