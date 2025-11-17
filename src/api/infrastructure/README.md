# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure project that deploys a scalable API
Gateway with Lambda functions, CloudFront distribution, and GitHub
self-hosted runner environment for the 10ulabs.com platform.

## Overview

This project provisions a complete serverless API infrastructure on AWS,
including API Gateway endpoints, Lambda functions, CloudFront distribution
for static documentation, and supporting infrastructure for GitHub
self-hosted runners using both ECS Fargate and EC2 instances.

## Key Features

- **API Gateway REST API** with custom domain and SSL certificate
- **Lambda Functions** for health checks, echo testing, and catch-all routing
- **CloudFront Distribution** for static documentation and API caching
- **GitHub Self-Hosted Runners** on ECS Fargate and EC2 spot instances
- **VPC Infrastructure** with public subnets and security groups
- **ECR Repository** for container image management
- **WAF Integration** for API protection
- **Automated DNS Management** with Route 53
- **Secrets Management** for GitHub tokens and webhook secrets

## Main Components

### Infrastructure Components

- **VPC**: Custom VPC with public subnets for runner workloads
- **ECS Cluster**: Container orchestration for Fargate-based runners
- **ECR Repository**: Docker image storage for GitHub runner containers
- **IAM Roles**: Granular permissions for EC2 and Fargate runners
- **Security Groups**: Network access controls for runner instances

### API Components

- **API Gateway**: RESTful API with OpenAPI specification
- **Lambda Functions**: Serverless compute for API endpoints
- **CloudFront**: CDN for API and static content delivery
- **S3 Bucket**: Static documentation hosting
- **WAF**: Web Application Firewall for API protection

### Monitoring & Security

- **CloudWatch Logs**: Centralized logging for all components
- **Secrets Manager**: Secure storage for GitHub tokens and secrets
- **SSL/TLS**: Automated certificate management via ACM
- **Access Logging**: Comprehensive request and access tracking

## Prerequisites

### System Requirements

- **Node.js** (v14 or later) - Required for AWS CDK
- **Python** (3.8 or later) - Runtime for CDK application
- **Git** - Version control and repository access

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0` - AWS CDK core library
- `constructs>=10.0.0,<11.0.0` - CDK constructs framework
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` - Type stubs for boto3
- `requests>=2.31.0` - HTTP library for API calls
- `types-requests>=2.31.0` - Type hints for requests
- `pyyaml>=6.0.1` - YAML parsing for OpenAPI specs
- `types-pyyaml>=6.0.12` - Type hints for PyYAML

### AWS Prerequisites

- AWS account with appropriate permissions
- Existing Route 53 hosted zone for the parent domain
- GitHub organization or repository for self-hosted runners
- GitHub personal access token with runner management permissions

## Configuration

### Main Configuration (`config.json`)

The project uses a centralized configuration file with the following structure:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 99,
      "nat_gateways": 0
    },
    "fargate_runners": {
      "cpu": "256",
      "memory": "512",
      "runner_labels": ["ephemeral-ecs-fargate-spot"]
    },
    "ec2_runners": {
      "spot_instance_types": ["t4g.large", "t4g.medium", "t4g.small"],
      "max_spot_price": "0.05"
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
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__"]
  }
}
```

### Required Secrets

Before deployment, create the following secrets in AWS Secrets Manager:

1. **GitHub Token Secret**: `github-runner/credentials`
   - Must contain a GitHub personal access token with repo and runner permissions

2. **Webhook Secret**: Automatically generated during deployment
   - Used for GitHub webhook signature verification

## Usage

### Installation

1. Clone the repository and navigate to the project directory:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK globally:

   ```bash
   npm install -g aws-cdk
   ```

### Configuration Setup

1. Update `config.json` with your specific values:
   - AWS account ID and region
   - Domain names for your deployment
   - GitHub organization and repository details

2. Create the GitHub token secret in AWS Secrets Manager:

   ```bash
   aws secretsmanager create-secret \
     --name "github-runner/credentials" \
     --description "GitHub token for self-hosted runners" \
     --secret-string "your-github-token"
   ```

### Deployment

1. Bootstrap CDK (first-time setup):

   ```bash
   cdk bootstrap
   ```

2. Review the deployment plan:

   ```bash
   cdk diff
   ```

3. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

4. After deployment, note the output values for API endpoints and resource ARNs.

### Using the Deployed API

Once deployed, the API provides the following endpoints:

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Endpoint**: `POST https://api.10ulabs.com/v1/echo`
- **API Documentation**: `GET https://api.10ulabs.com/`

Example API usage:

```bash
# Health check
curl https://api.10ulabs.com/health

# Echo test
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

### Managing Self-Hosted Runners

The infrastructure automatically provisions GitHub self-hosted runners:

- **Fargate Runners**: Ephemeral containers for lightweight workloads
- **EC2 Spot Instances**: Cost-effective runners for intensive tasks

Runners are automatically registered with your GitHub repository and can be
triggered through GitHub Actions workflows.

## Architecture Overview

### Infrastructure Flow

1. **VPC Setup**: Creates isolated network environment with public subnets
2. **Container Infrastructure**: ECS cluster and ECR repository for runners
3. **Security**: IAM roles, security groups, and secrets management
4. **Certificate**: SSL/TLS certificate for custom domain
5. **API Gateway**: REST API with Lambda function integrations
6. **CloudFront**: CDN distribution with multiple origins
7. **DNS**: Route 53 records pointing to CloudFront

### Request Flow

1. **Client Request** → CloudFront Distribution
2. **Behavior Matching** → Route to appropriate origin:
   - `/` → S3 bucket (documentation)
   - `/health`, `/v1/*` → API Gateway → Lambda functions
3. **API Gateway** → Lambda function execution
4. **Response** ← CloudFront ← Origin

### Runner Provisioning

1. **GitHub Webhook** → (Future: Lambda webhook handler)
2. **Runner Decision**: Fargate vs EC2 based on workload requirements
3. **Container/Instance Launch** with GitHub registration
4. **Job Execution** → Auto-termination after completion

### Security Architecture

- **WAF Protection**: Web Application Firewall on CloudFront
- **SSL/TLS**: End-to-end encryption with ACM certificates
- **IAM Roles**: Least-privilege access for all components
- **Secrets Manager**: Secure token and credential storage
- **VPC Security**: Network isolation and security groups

## Security Considerations

### Network Security

- VPC with public subnets only (no sensitive data in private subnets)
- Security groups with minimal required access
- CloudFront with WAF protection against common attacks

### Access Control

- IAM roles with least-privilege permissions
- Separate roles for Fargate and EC2 runners
- API Gateway with proper CORS configuration

### Secrets Management

- GitHub tokens stored in AWS Secrets Manager
- Webhook secrets auto-generated and encrypted
- Container environment variables from secure sources

### Monitoring and Logging

- CloudWatch logs for all Lambda functions and API Gateway
- ECS task logging for runner containers
- CloudFront access logs for request monitoring

## Troubleshooting

### Common Deployment Issues

**Certificate Validation Fails**:

- Ensure the parent domain hosted zone exists and is accessible
- Verify DNS propagation before deployment
- Check that the domain is not already in use

**Lambda Function Errors**:

- Check CloudWatch logs for specific error messages
- Verify function code and dependencies
- Ensure proper IAM permissions for function execution

**API Gateway Integration Issues**:

- Verify OpenAPI specification syntax
- Check Lambda function ARN substitutions
- Ensure proper stage deployment

### Runtime Issues

**Runners Not Starting**:

- Verify GitHub token permissions and validity
- Check ECS cluster capacity and subnet configuration
- Review ECR repository permissions and image availability

**API Endpoint Errors**:

- Check CloudFront behavior configurations
- Verify API Gateway stage deployment
- Review Lambda function logs for execution errors

**DNS Resolution Problems**:

- Confirm Route 53 record creation
- Check CloudFront distribution status
- Verify certificate association

### Debugging Commands

View CDK stack outputs:

```bash
aws cloudformation describe-stacks --stack-name TenULabsApi \
  --query 'Stacks[0].Outputs'
```

Check Lambda function logs:

```bash
aws logs tail /aws/lambda/TenULabsApi-HealthHandler --follow
```

Monitor ECS tasks:

```bash
aws ecs list-tasks --cluster TenULabsRunnerCluster
```
