# AWS Bedrock Configuration

A configuration file for AWS Bedrock API integration, defining essential
settings for interacting with Claude Sonnet models through Amazon's Bedrock
service.

## Overview

This project provides a structured configuration setup for applications that
integrate with AWS Bedrock's generative AI capabilities. The configuration
defines model parameters, token limits, and AWS service settings required
for Claude Sonnet API interactions.

## Purpose and Key Features

- **Centralized Configuration**: Single source of truth for AWS Bedrock
  settings
- **Token Management**: Configurable limits for reasoning and generation
  operations
- **Model Specification**: Defines specific Claude Sonnet model version and
  region
- **Environment Flexibility**: JSON-based configuration for easy environment
  management

## Main Components

### Configuration Schema

The `config.json` file contains the following key components:

- **AWS Account Settings**: Account ID and regional deployment configuration
- **Bedrock Model Configuration**: Claude Sonnet model specifications and
  token limits
- **Service Parameters**: API interaction settings and constraints

## Prerequisites and Requirements

### System Dependencies

- Python 3.7 or higher
- Valid AWS account with Bedrock access
- AWS credentials configured (IAM user or role with Bedrock permissions)

### AWS Permissions

Your AWS credentials must have the following permissions:

- `bedrock:InvokeModel`
- `bedrock:ListFoundationModels`

## Configuration Details

### AWS Settings

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1"
  }
}
```

- **account_id**: Target AWS account for Bedrock operations
- **region**: AWS region where Bedrock service is accessed

### Bedrock Model Configuration

```json
{
  "bedrock": {
    "max_tokens_reasoning": 4000,
    "max_tokens_generation": 16000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

- **max_tokens_reasoning**: Token limit for reasoning operations (4,000)
- **max_tokens_generation**: Token limit for content generation (16,000)
- **model_id**: Specific Claude Sonnet model version identifier

## Usage Instructions

### Installation Steps

1. Clone or download the configuration file to your project directory

2. Ensure your AWS credentials are configured using one of these methods:

   ```bash
   # Using AWS credentials file
   ~/.aws/credentials
   
   # Using environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

### Configuration Usage

Load the configuration in your Python application:

```python
import json

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Access settings
account_id = config['aws']['account_id']
region = config['aws']['region']
model_id = config['aws']['bedrock']['model_id']
max_tokens = config['aws']['bedrock']['max_tokens_generation']
```

### Environment Customization

Create environment-specific configurations:

```bash
# Development environment
config-dev.json

# Production environment  
config-prod.json

# Staging environment
config-staging.json
```

## Architecture Overview

### Configuration Flow

```text
Application → config.json → AWS Bedrock API → Claude Sonnet Model
```

1. **Configuration Loading**: Application reads settings from config.json
2. **AWS Authentication**: Uses configured credentials for API access
3. **Model Interaction**: Sends requests to specified Claude Sonnet model
4. **Response Handling**: Processes responses within configured token limits

### Authentication Flow

- AWS credentials authenticate API requests
- Regional endpoint routing based on configured region
- Model access controlled by Bedrock service permissions

### Data Integration

- Configuration parameters control API request formatting
- Token limits prevent excessive usage and costs
- Model ID ensures consistent AI model version usage

## Security Considerations

### Credential Management

- **Never commit AWS credentials** to version control
- Use IAM roles when running on AWS infrastructure
- Implement credential rotation policies
- Monitor AWS CloudTrail for API access logs

### Configuration Security

- Store sensitive configurations outside of source code
- Use AWS Secrets Manager for production credentials
- Implement least-privilege IAM policies
- Regular audit of Bedrock usage and costs

### Network Security

- Use VPC endpoints for Bedrock API access when possible
- Implement request rate limiting to prevent abuse
- Monitor unusual API usage patterns

## Troubleshooting Tips

### Common Issues

**Invalid Model ID Error**

```text
Error: Model not found or not accessible
```

- Verify model availability in your AWS region
- Check Bedrock service availability in specified region
- Ensure model ID format matches AWS documentation

**Authentication Failures**

```text
Error: Unable to locate credentials
```

- Verify AWS credentials are properly configured
- Check IAM permissions for Bedrock access
- Confirm account ID matches your AWS account

**Token Limit Exceeded**

```text
Error: Request exceeds maximum token limit
```

- Review and adjust max_tokens_reasoning and max_tokens_generation
- Optimize input text to reduce token usage
- Consider splitting large requests into smaller chunks

### Debugging Steps

1. Validate JSON configuration syntax
2. Test AWS credentials with simple Bedrock API call
3. Verify regional service availability
4. Check AWS service quotas and limits
5. Monitor CloudWatch logs for detailed error information

### Performance Optimization

- Adjust token limits based on use case requirements
- Consider regional latency when selecting AWS region
- Implement caching for frequently used model responses
- Monitor costs and optimize request patterns
