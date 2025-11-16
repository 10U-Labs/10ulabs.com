# AWS Bedrock Documentation Formatter

A Python-based infrastructure toolkit for automated technical documentation
formatting and generation using AWS Bedrock AI services. This project provides
intelligent markdown formatting capabilities and README generation for
technical documentation projects.

## Purpose and Key Features

This infrastructure enables automated documentation management through:

- **Intelligent Markdown Formatting**: Automatically formats CLAUDE.md files
  to comply with all markdownlint rules while preserving content integrity
- **AI-Powered README Generation**: Creates comprehensive README files by
  analyzing project code and configuration
- **AWS Bedrock Integration**: Leverages Claude Sonnet 4 model for advanced
  text processing and formatting
- **Retry Logic with Jitter**: Implements robust error handling and throttling
  protection for AWS API calls
- **Extended Reasoning**: Utilizes Bedrock's reasoning capabilities for
  complex documentation tasks

## Resources Created

This project creates and manages the following AWS resources:

- **AWS Bedrock Runtime Client**: Connects to Bedrock service in us-east-1
  region for AI model inference
- **Claude Sonnet 4 Model Access**: Uses
  `us.anthropic.claude-sonnet-4-20250514-v1:0` for text generation and
  formatting tasks

## Prerequisites and Requirements

### Python Dependencies

Since no `requirements.txt` file is present in the project, the following
standard library modules and AWS dependencies are required:

```txt
boto3>=1.26.0
botocore>=1.29.0
```

### System Dependencies

- **Python 3.7+**: Required for running the scripts
- **AWS Credentials**: Properly configured AWS credentials with Bedrock access
- **Internet Connection**: Required for AWS Bedrock API calls

### AWS Permissions

The following AWS IAM permissions are required:

- `bedrock:InvokeModel` - For Claude Sonnet 4 model access
- `bedrock:InvokeModelWithResponseStream` - For streaming responses (if used)

## Configuration Details

### config.json

The main configuration file contains:

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

#### Configuration Parameters

- **account_id**: AWS account identifier for resource management
- **region**: AWS region (us-east-1) where Bedrock service is accessed
- **bedrock.max_tokens**: Maximum tokens for content generation (16,000)
- **bedrock.max_tokens_reasoning**: Extended thinking budget tokens (4,000)
- **bedrock.model_id**: Specific Claude Sonnet 4 model version identifier

## Usage Instructions

### Installation Steps

1. Clone the repository and navigate to the project directory

2. Install required dependencies:

   ```bash
   pip install boto3 botocore
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

### Running the Infrastructure

#### Format CLAUDE.md File

To format an existing CLAUDE.md file with markdownlint compliance:

```bash
python3 format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000
```

#### Generate README Documentation

To check if README needs updating:

```bash
python3 scripts/readme.py \
  --check \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --output-file result.txt \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000
```

To update README automatically:

```bash
python3 scripts/readme.py \
  --update \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --output-file result.txt \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000
```

## Architecture Overview

### Component Interactions

1. **Configuration Layer**: `config.json` provides centralized settings for
   AWS account, region, and Bedrock model parameters

2. **Markdown Formatter** (`format_claude_md.py`):
   - Reads existing CLAUDE.md content
   - Sends formatting requests to Bedrock with detailed markdownlint rules
   - Applies intelligent formatting while preserving all original content
   - Writes compliant markdown back to file

3. **README Generator** (`scripts/readme.py`):
   - Scans project directories for all relevant files (Python, JSON, YAML)
   - Analyzes code structure and configuration
   - Uses Bedrock to assess README currency and generate updates
   - Implements intelligent content chunking for large projects

### Authentication and Authorization Flow

1. **AWS SDK Authentication**: Uses boto3 client with configured credentials
2. **Bedrock Service Access**: Authenticates to Bedrock runtime in us-east-1
3. **Model Authorization**: Accesses Claude Sonnet 4 model with proper
   permissions
4. **Retry Logic**: Implements exponential backoff with jitter for throttling

### Data Flows and Integrations

```
Input Files → Content Analysis → Bedrock AI Processing → Formatted Output
     ↓              ↓                    ↓                      ↓
CLAUDE.md    Text Extraction    Claude Sonnet 4      Updated CLAUDE.md
Project Files → Code Analysis → README Generation → Generated README.md
```

## Security Considerations

### Access Control

- **IAM Permissions**: Requires specific Bedrock model access permissions
- **Credential Management**: Uses AWS SDK credential chain for secure access
- **Network Security**: All communications use HTTPS/TLS with AWS services

### Data Privacy

- **Content Processing**: Input content is sent to AWS Bedrock for processing
- **No Persistent Storage**: Bedrock does not store conversation history
- **Regional Compliance**: Processing occurs within specified AWS region

### Security Best Practices

- Use IAM roles with least-privilege access for production deployments
- Implement credential rotation for long-running systems
- Monitor CloudTrail logs for Bedrock API usage
- Consider VPC endpoints for private network access

## Troubleshooting Tips

### Common Issues

#### Bedrock Throttling

```
ERROR: Bedrock throttled after 5 attempts
```

**Solution**: The scripts implement automatic retry with exponential backoff.
Wait and retry, or check AWS service limits.

#### Authentication Errors

```
ERROR: Unable to locate credentials
```

**Solutions**:

1. Verify AWS credentials configuration:

   ```bash
   aws sts get-caller-identity
   ```

2. Check IAM permissions for Bedrock access

3. Ensure correct region configuration (us-east-1)

#### File Not Found Errors

```
ERROR: CLAUDE.md not found
```

**Solution**: Ensure the target file exists in the current directory before
running formatting scripts.

#### JSON Parsing Errors

```
WARNING: Failed to parse JSON response from Bedrock
```

**Solution**: This triggers automatic fallback parsing. If persistent, check
Bedrock model availability and prompt formatting.

### Debug Logging

Enable detailed logging by modifying the logging configuration:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- **Jitter Implementation**: Random delays prevent thundering herd issues
- **Content Chunking**: Large files are processed in manageable segments
- **Token Limits**: Configured limits prevent excessive API usage
- **File Filtering**: Excludes test files and irrelevant content from analysis
