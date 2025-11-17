# Claude Markdown Formatter

This project provides an AWS Bedrock-powered tool for automatically formatting
and linting Markdown documents using Claude AI models. It specifically targets
formatting `CLAUDE.md` files to comply with markdownlint rules while
maintaining content quality and readability.

## Overview

The Claude Markdown Formatter leverages AWS Bedrock's Claude Sonnet model to
intelligently reformat Markdown documents. It includes retry logic for
handling API throttling, configurable token limits for both generation and
reasoning, and comprehensive error handling for production use.

## Key Features

- **AI-Powered Formatting**: Uses Claude Sonnet 4 via AWS Bedrock for
  intelligent Markdown formatting
- **Markdownlint Compliance**: Ensures output follows standard markdownlint
  rules
- **Retry Logic**: Implements exponential backoff with jitter for handling
  AWS API throttling
- **Extended Reasoning**: Supports Claude's reasoning capabilities with
  configurable token budgets
- **Production Ready**: Comprehensive logging and error handling

## Prerequisites and Requirements

### Python Dependencies

This project requires Python 3.7+ with the following package:

- `boto3` - AWS SDK for Python (Bedrock API access)

### System Dependencies

- **Python 3.7+**: Runtime environment for the formatter script
- **Git**: Version control for project management

### AWS Requirements

- AWS account with Bedrock service access
- IAM permissions for `bedrock-runtime:InvokeModel`
- Access to Claude Sonnet 4 model in specified AWS region

## Configuration

The project uses a JSON configuration file to manage AWS and Bedrock settings:

### config.json Structure

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

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `account_id` | AWS Account ID | 781581267945 |
| `region` | AWS Region for Bedrock | us-east-1 |
| `max_tokens` | Maximum tokens for generation | 16000 |
| `max_tokens_reasoning` | Reasoning budget tokens | 4000 |
| `model_id` | Claude Sonnet 4 model identifier | Latest version |

## Installation and Usage

### Step 1: Install Dependencies

```bash
pip install boto3
```

### Step 2: Configure AWS Credentials

Set up AWS credentials using one of these methods:

```bash
# Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Or use AWS credential files
aws configure
```

### Step 3: Prepare Input Files

Create a `CLAUDE.md` file in the project directory and a prompt template file
for formatting instructions.

### Step 4: Run the Formatter

```bash
python3 format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt_template.txt
```

### Command Line Arguments

- `--aws-region`: AWS region where Bedrock is available
- `--bedrock-model-id`: Specific Claude model version to use
- `--max-tokens-generation`: Token limit for content generation
- `--max-tokens-reasoning`: Token budget for extended thinking
- `--prompt-file`: Path to formatting instruction template

## Architecture Overview

### Component Interaction Flow

```text
[CLAUDE.md] → [format_claude_md.py] → [AWS Bedrock] → [Formatted CLAUDE.md]
                       ↓
                [config.json] ← [prompt_template.txt]
```

### Processing Pipeline

1. **Input Validation**: Script reads existing `CLAUDE.md` and validates
   configuration
2. **Prompt Construction**: Combines content with formatting instructions
   from template
3. **Bedrock API Call**: Sends formatted request to Claude Sonnet model
4. **Retry Logic**: Handles throttling with exponential backoff (5-30s
   initial jitter)
5. **Response Processing**: Extracts formatted content from API response
6. **Output Generation**: Writes corrected Markdown back to `CLAUDE.md`

### Authentication Flow

- Uses standard AWS credential chain (environment → credentials file → IAM
  roles)
- Requires `bedrock-runtime:InvokeModel` permission for specified model
- Regional endpoint routing based on configuration

### Data Flow

1. Local `CLAUDE.md` content is read into memory
2. Content is embedded in prompt template with formatting instructions
3. Request payload includes model configuration and reasoning settings
4. AWS Bedrock processes request using Claude Sonnet 4 reasoning
5. Formatted response replaces original file content

## Security Considerations

### AWS Permissions

Grant minimal required IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-sonnet-4-*"
    }
  ]
}
```

### Data Protection

- **Content Privacy**: Markdown content is sent to AWS Bedrock for processing
- **Credential Security**: Never commit AWS credentials to version control
- **Regional Compliance**: Use appropriate AWS regions for data residency
- **Logging**: Sensitive content is not logged; only metadata and errors

### Network Security

- All communication uses HTTPS/TLS encryption
- Bedrock API calls go through AWS backbone network
- No external dependencies beyond AWS services

## Troubleshooting

### Common Issues and Solutions

#### Bedrock Throttling

**Symptom**: `ThrottlingException` errors in logs

**Solution**: The script includes automatic retry with exponential backoff.
For persistent issues, consider:

```bash
# Increase initial jitter delay in script
# Or space out multiple runs
```

#### Missing Dependencies

**Symptom**: `ModuleNotFoundError: No module named 'boto3'`

**Solution**: Install required Python packages:

```bash
pip install boto3
```

#### Authentication Errors

**Symptom**: `NoCredentialsError` or `AccessDenied`

**Solutions**:

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions for Bedrock
aws iam simulate-principal-policy --policy-source-arn YOUR_ARN \
  --action-names bedrock:InvokeModel
```

#### Model Access Issues

**Symptom**: `ValidationException` for model ID

**Solution**: Verify model availability in your region:

- Check AWS Bedrock console for enabled models
- Ensure Claude Sonnet 4 access is granted
- Confirm model ID matches available versions

#### File Not Found Errors

**Symptom**: `FileNotFoundError: CLAUDE.md not found`

**Solution**: Ensure input file exists:

```bash
# Create empty file if needed
touch CLAUDE.md

# Or check current directory
ls -la *.md
```

### Debug Mode

Enable detailed logging by modifying the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

This provides additional information about API requests and responses for
troubleshooting complex issues.
