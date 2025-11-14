# 10U Labs API Infrastructure

A serverless AWS CDK infrastructure that creates a REST API with Lambda backend,
featuring custom domain support, SSL/TLS certificates, and comprehensive
logging. The infrastructure also includes components for GitHub self-hosted
runners using ECS Fargate and EC2.

## Overview

This CDK stack deploys a production-ready API Gateway REST API with Lambda
functions, custom domain configuration, and integrated logging. The API
provides health check and echo endpoints with CORS support enabled.

## Key Features

- **Serverless Architecture**: Lambda-based API handlers with API Gateway
- **Custom Domain**: SSL/TLS enabled subdomain with Route53 integration
- **Comprehensive Logging**: CloudWatch logs for API Gateway and Lambda
- **CORS Enabled**: Cross-origin resource sharing for web applications
- **Infrastructure as Code**: Fully defined using AWS CDK Python
- **Container Support**: ECS Fargate cluster for GitHub self-hosted runners
- **Security**: IAM roles, security groups, and secrets management

## Resources Created

### Core API Infrastructure

- **API Gateway REST API**: RESTful API with custom domain and SSL
- **Lambda Function**: Python 3.11 runtime with API request handling
- **ACM Certificate**: SSL/TLS certificate for secure HTTPS connections
- **Route53 A Record**: DNS alias record for custom subdomain
- **CloudWatch Log Groups**: Access logs and Lambda execution logs

### Supporting Infrastructure

- **VPC**: Isolated network with public subnets for containerized workloads
- **ECS Cluster**: Fargate cluster for running GitHub self-hosted runners
- **ECR Repository**: Container registry for runner Docker images
- **IAM Roles**: Service roles for EC2 and ECS tasks
- **Secrets Manager**: Secure storage for GitHub tokens and webhook secrets
- **Security Groups**: Network access controls for runner instances

## Prerequisites

Before deploying this infrastructure, ensure you have:

- **AWS Account**: With appropriate permissions for CDK deployment
- **AWS Credentials**: Configured via AWS CLI or environment variables
- **Node.js**: Version 14.x or later for AWS CDK CLI
- **Python**: Version 3.8 or later with pip
- **AWS CDK CLI**: Installed globally (`npm install -g aws-cdk`)
- **Parent Domain**: Existing Route53 hosted zone for domain validation

### Required Python Dependencies

```bash
pip install aws-cdk-lib constructs
```

## API Endpoints

The API provides the following endpoints:

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/health` | Health check endpoint | Service status |
| POST | `/v1/echo` | Echo request body | Echoed JSON data |
| ANY | `/{proxy+}` | Catch-all route | 404 Not Found |

### Health Check Endpoint

```bash
curl https://your-subdomain.example.com/health
```

**Response:**

```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

### Echo Endpoint

```bash
curl -X POST https://your-subdomain.example.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World"}'
```

**Response:**

```json
{
  "echo": {
    "message": "Hello World"
  },
  "received_at": "request-id-12345"
}
```

## Configuration

The stack requires a configuration dictionary with domain and AWS settings:

```python
config = {
    "domain_names": {
        "parent": "example.com",
        "subdomain": "api.example.com"
    },
    "aws": {
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 1,
            "subnet_configuration": {
                "public_subnet_cidr_mask": 24
            }
        },
        "fargate_runners": {
            "ecr_repository": "github-runners",
            "cpu": "256",
            "memory": "512",
            "runner_labels": ["fargate", "linux"]
        }
    },
    "naming": {
        "vpc_name": "10ulabs-vpc",
        "cluster_name": "github-runners",
        "task_family": "github-runner",
        "container_name": "runner",
        "log_stream_prefix": "runner",
        "github_token_secret_name": "github-token",
        "webhook_secret_name": "webhook-secret"
    },
    "github": {
        "repo": "organization/repository"
    }
}
```

## Deployment Instructions

1. **Clone the repository and navigate to the project directory:**

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Bootstrap CDK (first time only):**

   ```bash
   cdk bootstrap
   ```

4. **Create GitHub token secret in AWS Secrets Manager:**

   ```bash
   aws secretsmanager create-secret \
     --name "github-token" \
     --description "GitHub personal access token for runners" \
     --secret-string "your-github-token"
   ```

5. **Deploy the stack:**

   ```bash
   cdk deploy
   ```

6. **Verify deployment:**

   ```bash
   curl https://your-subdomain.example.com/health
   ```

## Testing the API

### Manual Testing

Test the health endpoint:

```bash
curl -v https://your-subdomain.example.com/health
```

Test the echo endpoint:

```bash
curl -X POST https://your-subdomain.example.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "timestamp": "2024-01-01T00:00:00Z"}'
```

### Error Handling

Test invalid JSON:

```bash
curl -X POST https://your-subdomain.example.com/v1/echo \
  -H "Content-Type: application/json" \
  -d 'invalid-json'
```

Test non-existent endpoint:

```bash
curl https://your-subdomain.example.com/nonexistent
```

## Architecture Notes

### Serverless Design

- **Lambda Functions**: Handle API requests with automatic scaling
- **API Gateway**: Manages routing, throttling, and request/response
- **Event-Driven**: Pay-per-request pricing model

### Security Features

- **SSL/TLS**: End-to-end encryption with ACM certificates
- **CORS**: Configured for cross-origin web application support
- **IAM Roles**: Least-privilege access for all services
- **VPC Isolation**: Network segmentation for containerized workloads

### Monitoring and Logging

- **Access Logs**: API Gateway request/response logging in CLF format
- **Lambda Logs**: Function execution logs with configurable retention
- **CloudWatch Integration**: Metrics and alarms for operational monitoring

### Scalability

- **Auto Scaling**: Lambda functions scale automatically with demand
- **Multi-AZ**: VPC spans multiple availability zones for resilience
- **Container Orchestration**: ECS Fargate for scalable runner instances

## Outputs

The stack exports the following values for use by other stacks:

- API Gateway URL and domain information
- VPC and subnet identifiers
- ECS cluster and task definition ARNs
- ECR repository details
- IAM role names and ARNs
- Secrets Manager secret names

These outputs enable integration with additional infrastructure components
and facilitate modular CDK stack composition.
