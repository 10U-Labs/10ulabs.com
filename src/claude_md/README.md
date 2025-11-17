# Claude Markdown Formatter

This project provides a Python-based tool for automatically formatting Markdown
documents using AWS Bedrock's Claude AI model. It's designed to ensure Markdown
files comply with markdownlint rules and maintain consistent formatting
standards.

## Purpose and Key Features

- **AI-Powered Formatting**: Leverages Claude AI through AWS Bedrock to
  intelligently format Markdown content
- **Markdownlint Compliance**: Ensures formatted documents meet standard
  Markdown linting rules
- **Retry Logic**: Implements exponential backoff and jittering to handle AWS
  API throttling gracefully
- **Extended Reasoning**: Supports Claude's extended thinking capabilities for
  more sophisticated formatting decisions
- **Error Handling**: Comprehensive error handling and logging for debugging

## Prerequisites and Requirements

### Python Dependencies

The following Python packages are required:

```python
boto3>=1.26.0
```

### System Dependencies

- **Python 3.7+**: Required for running the formatting script
- **AWS Account**: Valid AWS credentials configured for Bedrock access

### AWS Configuration

- AWS credentials configured (via AWS credentials file, IAM roles, or
  environment variables)
- Access to AWS Bedrock service in the specified region
- Permissions for the `bedrock-runtime:InvokeModel` action

## Configuration

The project uses a `config.json` file for configuration:

```json
{
  "account_id": 781581267945,
  "region": "us-east-1",
  "bedrock": {
    "max_tokens": 16000,
    "max_tokens_reasoning": 4000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

### Configuration Parameters

- **account_id**: AWS account ID for resource deployment
- **region**: AWS region where Bedrock service is accessed
- **bedrock.max_tokens**: Maximum tokens for content generation
- **bedrock.max_tokens_reasoning**: Maximum tokens for extended thinking
- **bedrock.model_id**: Specific Claude model version to use

## Installation and Usage

### Installation

1. Clone the repository and navigate to the project directory

2. Install Python dependencies:

   ```bash
   pip install boto3>=1.26.0
   ```

3. Configure AWS credentials using one of these methods:

   ```bash
   # Option 1: AWS credentials file
   aws configure
   
   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Running the Formatter

Execute the formatting script with required parameters:

```bash
python3 format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file path/to/prompt/template.txt
```

### Required Files

Before running the script, ensure these files exist:

- **CLAUDE.md**: The Markdown file to be formatted (input/output)
- **Prompt template file**: Contains formatting instructions for Claude

## Architecture Overview

### Component Interaction Flow

1. **Input Processing**: Script reads the existing `CLAUDE.md` file
2. **Prompt Generation**: Combines content with formatting instructions
3. **AI Processing**: Sends request to AWS Bedrock Claude model
4. **Response Handling**: Extracts formatted content from AI response
5. **Output Writing**: Overwrites original file with formatted content

### AWS Bedrock Integration

```python
# Example API call structure
response = bedrock_client.converse(
    modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
    messages=[{
        'role': 'user',
        'content': [{'text': formatted_prompt}]
    }],
    inferenceConfig={'maxTokens': 16000},
    additionalModelRequestFields={
        'reasoning_config': {
            'type': 'enabled',
            'budget_tokens': 4000
        }
    }
)
```

### Retry and Throttling Logic

The tool implements sophisticated retry logic:

- **Initial Jitter**: 5-30 second random delay to prevent thundering herd
- **Exponential Backoff**: Progressive delay increases for throttled requests
- **Maximum Retries**: Configurable retry limit (default: 5 attempts)
- **Error Classification**: Specific handling for throttling vs. other errors

## Security Considerations

### AWS Permissions

Ensure minimal required permissions for the AWS credentials:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/*"
    }
  ]
}
```

### Data Handling

- Markdown content is transmitted to AWS Bedrock for processing
- Ensure sensitive information is not included in files being formatted
- Consider data residency requirements when selecting AWS regions

### Credential Management

- Use IAM roles when running on AWS infrastructure
- Avoid hardcoding credentials in scripts or configuration files
- Regularly rotate access keys for programmatic access

## Troubleshooting

### Common Issues and Solutions

#### ThrottlingException Errors

```bash
# Symptoms: Bedrock throttled after N attempts
# Solution: Increase jitter range or reduce concurrent requests
```

#### No Text Blocks Found

```bash
# Symptoms: "No text blocks found in Bedrock response"
# Solution: Check model ID compatibility and prompt format
```

#### File Not Found Errors

```bash
# Symptoms: "CLAUDE.md not found"
# Solution: Ensure CLAUDE.md exists in current directory
```

#### Authentication Failures

```bash
# Symptoms: AWS credential errors
# Solutions:
# 1. Verify AWS credentials are properly configured
# 2. Check IAM permissions for Bedrock access
# 3. Confirm region availability for Bedrock service
```

### Debugging Tips

- Enable detailed logging by modifying the logging level:

  ```python
  logging.basicConfig(level=logging.DEBUG)
  ```

- Check AWS Bedrock service availability in your region
- Verify the model ID is correct and accessible
- Test with smaller content files to isolate issues
- Monitor AWS CloudTrail for detailed API call information

### Performance Optimization

- Adjust `max_tokens` values based on content size
- Consider regional latency when selecting AWS regions
- Implement content chunking for very large files
- Use appropriate instance types when running on AWS infrastructure
