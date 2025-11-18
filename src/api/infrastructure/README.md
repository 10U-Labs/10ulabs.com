# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure stack that deploys a scalable API Gateway with Lambda functions, CloudFront distribution, and GitHub self-hosted runner infrastructure.

## Overview

This project creates a production-ready API infrastructure on AWS with the following key features:

- **API Gateway**: RESTful API with OpenAPI specification
- **Lambda Functions**: Serverless endpoint handlers
- **CloudFront Distribution**: Global content delivery with custom domain
- **S3 Documentation**: Hosted API documentation with ReDoc
- **GitHub Runners**: Self-hosted runner infrastructure (Fargate + EC2)
- **Security**: WAF protection, SSL certificates, and IAM roles
- **Monitoring**: CloudWatch logs and metrics

## Architecture

The stack deploys:

1. **API Layer**: API Gateway with Lambda integrations for `/health`, `/v1/echo`, and catch-all routes
2. **Content Delivery**: CloudFront distribution serving both API endpoints and S3-hosted documentation
3. **Runner Infrastructure**: ECS Fargate cluster and EC2 instances for GitHub Actions
4. **Networking**: VPC with public subnets, security groups, and DNS configuration
5. **Storage**: ECR repository for runner images and S3 bucket for documentation

## Project Structure

```
├── app.py                    # CDK application entry point
├── stack.py                  # Main infrastructure stack definition
├── config.json              # Configuration parameters
├── requirements.txt          # Python dependencies
├── cdk.json                 # CDK configuration
├── endpoints/               # Lambda function source code
│   ├── health/              # Health check endpoint
│   ├── v1/echo/            # Echo endpoint for testing
│   └── catchall/           # Catch-all handler for undefined routes
└── test/                   # Test suites
    ├── test_unit.py        # Unit tests
    ├── test_integration.py # Integration tests
    └── test_e2e.py         # End-to-end tests
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9 or later
- AWS CDK v2 installed
- Docker (for building runner images)

## Configuration

The `config.json` file contains all deployment parameters:

```json
{
  "aws": {
    "account_id": "your-account-id",
    "region": "us-east-1",
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

## Deployment

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

3. **Bootstrap CDK** (first time only):
   ```bash
   cdk bootstrap
   ```

4. **Deploy the stack**:
   ```bash
   cdk deploy
   ```

## API Endpoints

The deployed API provides the following endpoints:

### Health Check
- **GET** `/health`
- Returns service health status
- Used for monitoring and load balancer health checks

### Echo Service
- **POST** `/v1/echo`
- Echoes back the request payload with metadata
- Useful for testing and debugging

### Documentation
- **GET** `/` - Interactive API documentation (ReDoc)
- **GET** `/openapi.yaml` - OpenAPI specification

## GitHub Runner Infrastructure

The stack includes infrastructure for GitHub self-hosted runners:

### Fargate Runners
- ECS Fargate tasks for containerized runners
- ECR repository for runner Docker images
- Automatic scaling based on workflow demands

### EC2 Runners
- Spot instances for cost-effective compute
- IAM roles with ECR access and self-termination permissions
- Security groups for network isolation

### Secrets Management
- GitHub token stored in AWS Secrets Manager
- Webhook secrets for secure communication

## Testing

The project includes comprehensive test suites:

```bash
# Unit tests
pytest test/test_unit.py

# Integration tests
pytest test/test_integration.py

# End-to-end tests
pytest test/test_e2e.py
```

## Monitoring and Logging

- **CloudWatch Logs**: All Lambda functions and API Gateway logs
- **CloudWatch Metrics**: API Gateway metrics and custom metrics
- **Access Logs**: CloudFront and API Gateway access logging
- **Log Retention**: Configurable retention periods (default: 1 week for functions, 1 month for API)

## Security Features

- **WAF Protection**: Web Application Firewall for CloudFront
- **SSL/TLS**: Automatic certificate management via ACM
- **IAM Roles**: Least-privilege access for all components
- **VPC Security**: Network isolation with security groups
- **S3 Security**: Block public access, encryption at rest

## Cost Optimization

- **Serverless Architecture**: Pay-per-use Lambda functions
- **Spot Instances**: Cost-effective EC2 runners
- **CloudFront Caching**: Reduced origin requests
- **No NAT Gateways**: Public-only subnets for cost savings

## Cleanup

To destroy all resources:

```bash
cdk destroy
```

**Warning**: This will permanently delete all resources including S3 buckets and their contents.

## Stack Outputs

The stack exports several values for use by other stacks:

- `TenULabsApi-Endpoint`: The API endpoint URL
- `TenULabsApi-VpcId`: VPC ID for runner infrastructure
- `TenULabsApi-ClusterArn`: ECS cluster ARN
- `TenULabsApi-EcrRepositoryUri`: ECR repository for runner images

## Development

### Adding New Endpoints

1. Create a new directory under `endpoints/`
2. Add a `handler.py` file with the Lambda function
3. Update `stack.py` to include the new Lambda function
4. Update `openapi.yaml` with the new endpoint specification
5. Add tests in the appropriate test files

### Modifying Infrastructure

1. Update `stack.py` with new resources
2. Modify `config.json` if new parameters are needed
3. Update tests to cover new functionality
4. Run `cdk diff` to preview changes before deployment

## Troubleshooting

### Common Issues

1. **Certificate Validation**: Ensure the parent domain's hosted zone is accessible
2. **Lambda Permissions**: Check that API Gateway has invoke permissions
3. **CloudFront Caching**: Use cache invalidation for immediate updates
4. **ECR Access**: Verify IAM roles have ECR permissions for runner instances

### Debugging

- Check CloudWatch logs for Lambda function errors
- Use AWS X-Ray for distributed tracing
- Monitor CloudWatch metrics for performance issues
- Review API Gateway execution logs for request/response details
