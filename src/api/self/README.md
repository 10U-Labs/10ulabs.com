# 10U Labs API Infrastructure

This AWS CDK project deploys a comprehensive cloud infrastructure for the 10U
Labs API, including API Gateway, Lambda functions, and GitHub self-hosted
runner capabilities using both AWS Fargate and EC2 instances.

## Purpose and Key Features

- **REST API**: Serverless API Gateway with Lambda backend for health checks
  and echo services
- **Custom Domain**: SSL-enabled custom domain with Route53 DNS management
- **GitHub Runners**: Self-hosted GitHub Actions runners on AWS Fargate and EC2
- **Container Registry**: Private ECR repository for runner Docker images
- **Networking**: Dedicated VPC with public subnets for isolated workloads
- **Security**: IAM roles, security groups, and AWS Secrets Manager integration
- **Monitoring**: CloudWatch logging for API Gateway and Lambda functions

## Resources Created

### Networking & Security

- **VPC**: Dedicated virtual private cloud with configurable CIDR and AZs
- **Public Subnets**: Internet-accessible subnets for runner workloads
- **Security Group**: Outbound-only access for self-hosted runners
- **IAM Roles**: EC2 runner role with ECR access and self-termination
  permissions
- **Instance Profile**: EC2 instance profile for GitHub runner instances

### API Infrastructure

- **Lambda Function**: Python 3.11 function handling API requests
- **API Gateway**: REST API with custom domain and CORS configuration
- **SSL Certificate**: ACM certificate with DNS validation
- **Route53 Record**: A record pointing custom domain to API Gateway
- **CloudWatch Logs**: Log groups for API access logs and Lambda execution

### Container & Compute

- **ECR Repository**: Private repository for self-hosted runner images
- **ECS Cluster**: Fargate cluster for containerized GitHub runners
- **Task Definition**: Fargate task definition with GitHub token integration
- **Secrets Manager**: Webhook secret and GitHub token storage

### API Endpoints

- `GET /health`: Health check endpoint returning service status
- `POST /v1/echo`: Echo service returning request body with metadata
- `ANY /{proxy+}`: Catch-all route for undefined endpoints

## Prerequisites and Requirements

### Python Dependencies

Install the required Python packages:

```bash
pip install aws-cdk-lib==2.150.0
pip install "constructs>=10.0.0,<11.0.0"
pip install "boto3>=1.34.0"
pip install "boto3-stubs[route53,route53domains,account,organizations]>=1.34.0"
pip install "requests>=2.31.0"
pip install "types-requests>=2.31.0"
```

### System Dependencies

- **Node.js** (v16 or later): Required for AWS CDK CLI
- **Python** (3.8 or later): For CDK application and Lambda functions
- **Git**: For repository operations

### AWS Requirements

- AWS account with appropriate permissions
- AWS credentials configured (via environment variables, AWS profile, or IAM
  roles)
- Existing Route53 hosted zone for parent domain
- GitHub token stored in AWS Secrets Manager

## Configuration

Create a `config.json` file with the following structure:

```json
{
  "aws": {
    "account_id": "123456789012",
    "region": "us-east-1",
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 2,
      "nat_gateways": 0,
      "subnet_configuration": {
        "public_subnet_cidr_mask": 24
      }
    },
    "fargate_runners": {
      "ecr_repository": "github-runner",
      "cpu": "1024",
      "memory": "2048",
      "runner_labels": ["fargate", "linux"]
    }
  },
  "domain_names": {
    "parent": "example.com",
    "subdomain": "api.example.com"
  },
  "naming": {
    "vpc_name": "10ulabs-vpc",
    "cluster_name": "github-runners",
    "task_family": "github-runner",
    "container_name": "runner",
    "log_stream_prefix": "github-runner",
    "github_token_secret_name": "github-token",
    "webhook_secret_name": "github-webhook-secret"
  },
  "github": {
    "repo": "organization/repository"
  }
}
```

## Usage Instructions

### Installation

1. Clone the repository and navigate to the project directory:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Install dependencies:

   ```bash
   npm install -g aws-cdk
   pip install -r requirements.txt
   ```

3. Configure AWS credentials and create the configuration file as shown above.

### Deployment

1. Bootstrap CDK (first time only):

   ```bash
   cdk bootstrap
   ```

2. Deploy the infrastructure:

   ```bash
   python app.py
   cdk deploy
   ```

3. Verify API propagation:

   ```bash
   python poll_api_until_it_has_propagated.py https://api.example.com
   ```

### Using the API

Test the health endpoint:

```bash
curl https://api.example.com/health
```

Test the echo endpoint:

```bash
curl -X POST https://api.example.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

### Managing GitHub Runners

The infrastructure creates resources for both Fargate and EC2 GitHub runners.
Use the exported CloudFormation outputs to integrate with webhook handlers or
CI/CD pipelines that spawn runners on demand.

## Architecture Overview

### API Flow

1. **DNS Resolution**: Route53 resolves custom domain to API Gateway
2. **SSL Termination**: ACM certificate handles HTTPS encryption
3. **Request Routing**: API Gateway routes requests to Lambda function
4. **Response**: Lambda processes requests and returns JSON responses

### Runner Infrastructure

1. **Container Registry**: ECR stores runner Docker images
2. **Fargate Execution**: ECS runs containerized runners with GitHub token
   access
3. **EC2 Alternative**: Instance profile enables EC2-based runners with
   self-termination
4. **Networking**: VPC provides isolated environment for runner workloads

### Security Model

- **Secrets Management**: GitHub tokens and webhook secrets stored in AWS
  Secrets Manager
- **IAM Permissions**: Least-privilege roles for runners and Lambda functions
- **Network Isolation**: VPC with security groups controlling traffic flow
- **Resource Tagging**: Consistent tagging for resource management and cost
  tracking

## Security Considerations

### Access Control

- Lambda functions use AWS managed execution roles
- EC2 runners limited to ECR access and self-termination
- Fargate tasks use task roles for container-level permissions
- All secrets encrypted at rest in AWS Secrets Manager

### Network Security

- Security groups deny all inbound traffic by default
- Outbound internet access required for GitHub API communication
- No direct SSH access to runner instances
- VPC Flow Logs can be enabled for network monitoring

### Operational Security

- CloudWatch logging enabled for audit trails
- ECR image scanning detects vulnerabilities
- Short-lived runner instances minimize attack surface
- Resource cleanup through lifecycle rules and removal policies

## Troubleshooting

### Common Issues

**API Gateway 403 Errors**:

- Verify SSL certificate validation completed
- Check Route53 DNS propagation
- Confirm API Gateway deployment succeeded

**Lambda Timeout Errors**:

- Review CloudWatch logs for function errors
- Verify handler code syntax and imports
- Check function timeout configuration (currently 30 seconds)

**Runner Connection Issues**:

- Verify GitHub token permissions in Secrets Manager
- Check security group outbound rules allow HTTPS (port 443)
- Confirm ECR repository contains valid runner image

**CDK Deployment Failures**:

- Verify AWS credentials and permissions
- Check for existing resources with same names
- Review CloudFormation stack events for detailed error messages

### Monitoring and Debugging

Use AWS CloudWatch to monitor:

- API Gateway access logs and error rates
- Lambda function duration and error counts
- ECS task startup and termination events
- VPC Flow Logs for network troubleshooting

Export CloudFormation outputs provide resource identifiers for integration
with monitoring tools and additional infrastructure components.
