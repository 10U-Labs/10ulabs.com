# TenULabs API Infrastructure

A comprehensive AWS CDK infrastructure stack that deploys a serverless API
Gateway with Lambda functions, CloudFront distribution, and GitHub
self-hosted runner infrastructure for the 10ulabs.com platform.

## Overview

This infrastructure creates a production-ready API platform with the
following key capabilities:

- **API Gateway**: RESTful API with health check and echo endpoints
- **Lambda Functions**: Serverless compute for API endpoints
- **CloudFront Distribution**: Global CDN for API and documentation
- **GitHub Runners**: Self-hosted runner infrastructure (Fargate + EC2)
- **Custom Domain**: SSL-enabled custom domain with Route 53
- **Security**: WAF protection, VPC isolation, and IAM controls

## Purpose and Key Features

- Deploy a scalable API infrastructure at `api.10ulabs.com`
- Provide GitHub self-hosted runners for CI/CD workflows
- Serve API documentation from S3 through CloudFront
- Enable secure webhook handling for GitHub automation
- Support both Fargate and EC2 spot instance runners
- Implement comprehensive logging and monitoring

## Resources Created

### Core API Infrastructure

- **API Gateway**: REST API with custom domain and SSL certificate
- **Lambda Functions**: Health check, echo, and catch-all handlers
- **CloudFront Distribution**: CDN with custom caching policies
- **Route 53 Records**: DNS alias records for custom domain
- **ACM Certificate**: SSL certificate for HTTPS endpoints

### Storage and Content

- **S3 Bucket**: Documentation and static content storage
- **S3 Bucket Deployment**: Automated deployment of API docs

### Compute Infrastructure

- **VPC**: Isolated network with public subnets
- **ECS Cluster**: Container orchestration for Fargate runners
- **ECR Repository**: Docker image registry for runner containers
- **Fargate Task Definition**: Containerized runner configuration

### Security and Access

- **IAM Roles**: Execution roles for Lambda, ECS, and EC2 runners
- **Security Groups**: Network access controls
- **Secrets Manager**: GitHub tokens and webhook secrets
- **WAF Web ACL**: Application firewall protection

### Monitoring and Logging

- **CloudWatch Log Groups**: Centralized logging for all services
- **CloudWatch Metrics**: Performance monitoring and alerting

## Prerequisites

### System Dependencies

- **Python 3.8+**: Required for AWS CDK and project scripts
- **Node.js 14+**: Required for AWS CDK CLI and tooling
- **Git**: Version control and repository access

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Key Dependencies

- `aws-cdk-lib==2.150.0`: AWS CDK framework
- `constructs>=10.0.0,<11.0.0`: CDK constructs library
- `boto3>=1.34.0`: AWS SDK for Python
- `requests>=2.31.0`: HTTP library for API calls
- `pyyaml>=6.0.1`: YAML configuration parsing

### AWS Setup

- **AWS Account**: Valid AWS account with appropriate permissions
- **AWS Credentials**: Configured via AWS SDK (environment variables,
  IAM roles, or credential files)
- **Route 53 Hosted Zone**: Existing hosted zone for parent domain

## Configuration

The infrastructure is configured through `config.json` and `cdk.json`
files:

### Main Configuration (`config.json`)

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "vpc": {
      "cidr": "10.0.0.0/16",
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

```json
{
  "app": "python3 app.py",
  "context": {
    "@aws-cdk/core:stackRelativeExports": true
  }
}
```

### Key Configuration Sections

- **AWS Settings**: Account, region, and service configurations
- **VPC Configuration**: Network topology and subnet layout
- **Domain Names**: Custom domain and SSL certificate settings
- **GitHub Integration**: Repository and organization settings
- **Runner Configuration**: Fargate and EC2 runner specifications

## Usage Instructions

### Installation

1. **Clone the repository and navigate to the project directory**

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install AWS CDK CLI:**

   ```bash
   npm install -g aws-cdk
   ```

4. **Configure AWS credentials** (one of the following):
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - AWS credential files: `~/.aws/credentials`
   - IAM roles for EC2/Lambda execution

### Deployment

1. **Bootstrap CDK (first time only):**

   ```bash
   cdk bootstrap aws://781581267945/us-east-1
   ```

2. **Synthesize the CloudFormation template:**

   ```bash
   cdk synth
   ```

3. **Deploy the infrastructure:**

   ```bash
   cdk deploy
   ```

4. **Verify deployment:**

   ```bash
   curl https://api.10ulabs.com/health
   ```

### Managing the Infrastructure

**View stack outputs:**

```bash
cdk ls --json
```

**Update configuration and redeploy:**

```bash
# Edit config.json as needed
cdk diff
cdk deploy
```

**Destroy the infrastructure:**

```bash
cdk destroy
```

### Using the Deployed API

**Health Check:**

```bash
curl https://api.10ulabs.com/health
```

**Echo Endpoint:**

```bash
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

**API Documentation:**

Visit <https://api.10ulabs.com/> for interactive API documentation.

## Architecture Overview

### API Request Flow

1. **Client Request**: HTTPS request to `api.10ulabs.com`
2. **CloudFront**: CDN processes request with caching rules
3. **Origin Routing**: Routes to API Gateway or S3 based on path
4. **API Gateway**: Validates request and routes to Lambda
5. **Lambda Execution**: Processes business logic and returns response
6. **Response Caching**: CloudFront caches appropriate responses

### GitHub Runner Flow

1. **Webhook Trigger**: GitHub sends workflow webhook
2. **Lambda Handler**: Processes webhook and validates signature
3. **Runner Launch**: Starts Fargate task or EC2 spot instance
4. **Job Execution**: Runner picks up and executes GitHub workflow
5. **Cleanup**: Ephemeral runner terminates after job completion

### Authentication and Authorization

- **API Gateway**: No authentication (public endpoints)
- **GitHub Integration**: Token-based authentication via Secrets Manager
- **AWS Resources**: IAM roles with least-privilege access
- **CloudFront**: WAF protection against common attacks

### Data Flows

- **Static Content**: S3 → CloudFront → Client
- **API Requests**: Client → CloudFront → API Gateway → Lambda
- **Runner Logs**: ECS/EC2 → CloudWatch Logs
- **Secrets**: Secrets Manager → Lambda/ECS runtime

## Security Considerations

### Network Security

- **VPC Isolation**: Runners execute in dedicated VPC
- **Security Groups**: Restrictive ingress, permissive egress
- **Public Subnets**: Only for outbound internet access
- **No NAT Gateways**: Cost optimization with direct internet access

### Access Control

- **IAM Roles**: Separate roles for each service component
- **Least Privilege**: Minimal permissions for each use case
- **Resource Tagging**: Consistent tagging for access control
- **Cross-Account**: Stack exports for resource sharing

### Data Protection

- **Secrets Management**: GitHub tokens in AWS Secrets Manager
- **SSL/TLS**: End-to-end encryption for all API traffic
- **S3 Encryption**: Server-side encryption for static content
- **Log Retention**: Configurable retention for compliance

### Application Security

- **WAF Protection**: Application-layer firewall rules
- **Input Validation**: Lambda function input sanitization
- **Error Handling**: Secure error responses without data leakage
- **CORS Configuration**: Appropriate cross-origin policies

## Troubleshooting

### Common Issues

**CDK Bootstrap Errors:**

```bash
# Ensure AWS credentials are configured
aws sts get-caller-identity
cdk bootstrap --force
```

**Domain Certificate Issues:**

- Verify Route 53 hosted zone exists for parent domain
- Check DNS propagation: `dig api.10ulabs.com`
- Certificate validation may take 5-10 minutes

**Lambda Function Errors:**

```bash
# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/"
```

**GitHub Runner Problems:**

- Verify GitHub token has proper permissions
- Check ECS task logs in CloudWatch
- Ensure ECR repository contains runner image

### Performance Issues

**API Response Times:**

- Check CloudFront cache hit rates
- Review Lambda function memory allocation
- Monitor API Gateway throttling metrics

**Runner Launch Delays:**

- Verify ECS cluster capacity
- Check EC2 spot instance availability
- Review Fargate task startup times

### Monitoring Commands

**Stack Status:**

```bash
cdk ls
aws cloudformation describe-stacks --stack-name TenULabsApi
```

**Resource Health:**

```bash
# API Gateway
aws apigateway get-rest-apis

# CloudFront Distribution
aws cloudfront list-distributions

# ECS Cluster
aws ecs describe-clusters --clusters TenULabsRunnerCluster
```
