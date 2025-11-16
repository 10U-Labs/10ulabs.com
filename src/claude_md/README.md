# Claude Markdown Formatter

A Python utility toolkit for automatically formatting and generating technical
documentation using AWS Bedrock's Claude models. This project provides scripts
for formatting CLAUDE.md files to comply with markdownlint rules and
generating comprehensive README.md files for infrastructure projects.

## Purpose and Key Features

- **Automated Markdown Formatting**: Reformats CLAUDE.md files to comply with
  all markdownlint rules while preserving 100% of original content
- **Intelligent README Generation**: Automatically generates comprehensive
  README.md files by analyzing project infrastructure code
- **README Currency Checking**: Validates existing README files for accuracy
  and completeness against current codebase
- **AWS Bedrock Integration**: Leverages Claude Sonnet models for intelligent
  document processing and generation
- **Robust Error Handling**: Implements exponential backoff retry logic for
  AWS API throttling and errors

## Resources Created

This project does not create AWS infrastructure resources. Instead, it
utilizes existing AWS services:

- **AWS Bedrock Runtime**: For accessing Claude AI models to process and
  generate documentation
- **IAM Permissions**: Requires bedrock:InvokeModel permissions for the
  specified Claude model

## Prerequisites and Requirements

### Python Dependencies

No requirements.txt file found in the project. The following dependencies are
inferred from the code:

- **boto3**: AWS SDK for Python (Bedrock API interactions)
- **botocore**: Core library for boto3 (exception handling)

### System Dependencies

- **Python 3.6+**: Required for f-string formatting and type hints
- **AWS Credentials**: Configured via AWS CLI, environment variables, or IAM
  roles

### AWS Configuration

- Valid AWS credentials with Bedrock permissions
- Access to Claude Sonnet models in AWS Bedrock
- Appropriate IAM permissions for bedrock-runtime:InvokeModel

## Configuration

### config.json

```json
{
  "account_id": 781581267945,
  "region": "us-east-1",
  "bedrock": {
    "max_tokens": 16000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

Configuration parameters:

- **account_id**: AWS account ID (informational)
- **region**: AWS region for Bedrock service
- **bedrock.max_tokens**: Maximum tokens for Claude model responses
- **bedrock.model_id**: Specific Claude Sonnet model version to use

## Usage Instructions

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd claude-markdown-formatter
   ```

2. Install Python dependencies:

   ```bash
   pip install boto3 botocore
   ```

3. Configure AWS credentials:

   ```bash
   aws configure
   ```

   Or set environment variables:

   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Formatting CLAUDE.md Files

Format an existing CLAUDE.md file to comply with markdownlint rules:

```bash
python3 format_claude_md.py --aws-region us-east-1
```

Optional parameters:

```bash
python3 format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens 16000
```

### Generating README Files

Check if a README needs updating:

```bash
python3 scripts/readme.py \
  --check \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --output-file check_result.txt
```

Generate or update a README file:

```bash
python3 scripts/readme.py \
  --update \
  --project-dir /path/to/project \
  --aws-region us-east-1
```

Advanced options:

```bash
python3 scripts/readme.py \
  --update \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generate 16000 \
  --max-tokens-check 200
```

## Architecture Overview

### Component Interaction

1. **Configuration Loading**: Scripts read config.json for default AWS and
   Bedrock settings
2. **File Discovery**: README generator automatically discovers project files
   using glob patterns
3. **Bedrock Communication**: Both scripts use the same retry mechanism for
   robust API communication
4. **Content Processing**: Claude models analyze and process documentation
   according to specific prompts
5. **Output Generation**: Processed content is written back to files with
   proper formatting

### Authentication Flow

1. Scripts initialize boto3 Bedrock Runtime client with specified region
2. AWS credentials are resolved via standard boto3 credential chain:
   - Environment variables
   - AWS credentials file
   - IAM roles (for EC2/Lambda execution)
3. Bedrock API calls are made with exponential backoff retry logic
4. Throttling exceptions trigger automatic retry with jitter

### Data Flows

1. **Input Processing**: Original content is read from files and combined
   with detailed formatting/generation prompts
2. **AI Processing**: Claude models receive structured prompts with specific
   requirements and constraints
3. **Output Validation**: Generated content is validated for completeness
   and proper formatting
4. **File Operations**: Processed content replaces original files atomically

## Security Considerations

### AWS Permissions

Ensure IAM policies follow least privilege principles:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-sonnet-4-20250514-v1:0"
      ]
    }
  ]
}
```

### Data Handling

- File contents are sent to AWS Bedrock for processing
- Ensure sensitive information is not included in processed files
- Consider data residency requirements for your region
- No persistent storage of file contents in AWS services

### Credential Management

- Never commit AWS credentials to version control
- Use IAM roles when running on AWS infrastructure
- Rotate access keys regularly for programmatic access
- Monitor CloudTrail logs for Bedrock API usage

## Troubleshooting

### Common Issues

**AWS Credentials Not Found**:

- Verify AWS credentials are configured correctly
- Check environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- Ensure IAM user/role has bedrock:InvokeModel permissions

**Bedrock Throttling**:

- Scripts include automatic retry with exponential backoff
- Monitor CloudWatch metrics for Bedrock usage limits
- Consider implementing additional rate limiting for batch operations

**Model Access Denied**:

- Verify the specified Claude model is available in your region
- Check if model access has been granted in Bedrock console
- Ensure account has access to Anthropic models

**File Processing Errors**:

- Check file encoding (scripts expect UTF-8)
- Verify file permissions for read/write operations
- Ensure config.json exists and is valid JSON

### Debug Information

Enable verbose logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

Monitor Bedrock API calls in CloudTrail for detailed error information.

### Performance Optimization

- Use appropriate max_tokens values to balance cost and functionality
- Implement batching for processing multiple files
- Consider caching results for frequently processed content
- Monitor token usage to optimize cost efficiency
