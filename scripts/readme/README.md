# AWS Bedrock Configuration Project

A simple configuration management project for AWS Bedrock AI services that
provides standardized settings for model parameters and regional deployment.

## Overview

This project contains configuration files for AWS Bedrock AI model deployment,
specifically configured for Claude Sonnet model usage in the us-east-1 region.
It provides a centralized way to manage Bedrock model parameters including
token limits and model identifiers.

## Key Features

- Centralized AWS Bedrock configuration management
- Support for Claude Sonnet AI model
- Configurable token limits for reasoning and generation
- Regional AWS deployment settings
- JSON-based configuration for easy modification

## Resources

This configuration project manages settings for the following AWS resources:

- **AWS Bedrock**: AI service configuration for model deployment
- **Claude Sonnet Model**: Specific model configuration
  (us.anthropic.claude-sonnet-4-20250514-v1:0)

## Prerequisites and Requirements

### Python Environment

- Python 3.7 or higher

### System Dependencies

- Git (for version control)
- Text editor or IDE for configuration management

### AWS Account Requirements

- Valid AWS account with access to account ID: 781581267945
- AWS Bedrock service access in us-east-1 region
- Appropriate IAM permissions for Bedrock model usage

## Configuration Details

### Main Configuration (config.json)

The project uses a single configuration file with the following structure:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_reasoning": 4000,
      "max_tokens_generation": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  }
}
```

### Configuration Parameters

| Parameter | Value | Description |
| --- | --- | --- |
| account_id | 781581267945 | Target AWS account identifier |
| region | us-east-1 | AWS deployment region |
| max_tokens_reasoning | 4000 | Token limit for reasoning operations |
| max_tokens_generation | 16000 | Token limit for text generation |
| model_id | claude-sonnet-4 | Specific Bedrock model identifier |

## Usage Instructions

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Verify configuration file integrity:

   ```bash
   cat config.json
   ```

### Configuration Management

1. **Modify Model Parameters**:

   Edit the `config.json` file to adjust token limits:

   ```json
   {
     "aws": {
       "bedrock": {
         "max_tokens_reasoning": 5000,
         "max_tokens_generation": 20000
       }
     }
   }
   ```

2. **Update Region Settings**:

   Change the deployment region as needed:

   ```json
   {
     "aws": {
       "region": "us-west-2"
     }
   }
   ```

3. **Validate JSON Format**:

   Use a JSON validator to ensure configuration integrity:

   ```bash
   python -m json.tool config.json
   ```

### Using the Configuration

Applications can load and use this configuration:

```python
import json

with open('config.json', 'r') as f:
    config = json.load(f)

# Access Bedrock settings
bedrock_config = config['aws']['bedrock']
model_id = bedrock_config['model_id']
max_tokens = bedrock_config['max_tokens_generation']
```

## Architecture Overview

### Configuration Flow

1. **Configuration Loading**: Applications read settings from config.json
2. **AWS Integration**: Settings are used to configure Bedrock API calls
3. **Model Interaction**: Token limits control AI model behavior
4. **Regional Deployment**: All resources operate in specified AWS region

### Component Interactions

```text
config.json → Application Code → AWS Bedrock API → Claude Model
```

### Data Flow

- Configuration parameters flow from JSON file to application runtime
- Token limits control request/response sizes with Bedrock models
- Regional settings ensure consistent deployment geography

## Security Considerations

### Configuration Security

- **Sensitive Data**: Account ID is exposed in configuration
- **Access Control**: Limit file system access to configuration files
- **Version Control**: Consider using environment variables for sensitive data

### AWS Security

- **IAM Permissions**: Ensure minimal required permissions for Bedrock access
- **Model Access**: Verify appropriate model usage permissions
- **Regional Compliance**: Confirm data residency requirements in us-east-1

### Best Practices

- Store sensitive configuration in AWS Systems Manager Parameter Store
- Use IAM roles instead of access keys where possible
- Enable CloudTrail logging for Bedrock API usage
- Regularly rotate credentials and review access patterns

## Troubleshooting

### Common Issues

**Invalid JSON Format**:

```bash
# Validate JSON syntax
python -m json.tool config.json
```

**Missing Configuration Values**:

- Verify all required fields are present in config.json
- Check for typos in parameter names
- Ensure numeric values are not quoted

**AWS Access Issues**:

- Confirm AWS account permissions for Bedrock service
- Verify region availability for specified model
- Check account ID matches your AWS account

### Configuration Validation

Create a simple validation script:

```python
import json
import sys

required_keys = ['aws.account_id', 'aws.region', 'aws.bedrock.model_id']

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    print("Configuration loaded successfully")
except Exception as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### Model Access Verification

Test Bedrock model availability:

- Check AWS Bedrock console for model access in your region
- Verify model ID format matches AWS documentation
- Confirm token limits are within model constraints
