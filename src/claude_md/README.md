# Bedrock Documentation Generator

A Python-based tool for generating and maintaining technical documentation
using AWS Bedrock's Claude model. This project provides scripts to
automatically generate README files and format markdown documentation with
AI assistance.

## Purpose and Key Features

This infrastructure enables automated documentation generation and formatting
for technical projects using AWS Bedrock. Key features include:

- **Intelligent README Generation**: Analyzes project files to create
  comprehensive documentation
- **Markdown Formatting**: Ensures markdownlint compliance for all generated
  content  
- **AWS Bedrock Integration**: Leverages Claude models for high-quality text
  generation
- **Retry Logic**: Implements exponential backoff for API throttling
- **Extended Reasoning**: Supports Claude's reasoning capabilities for better
  output quality

## Resources Created

This project uses the following AWS resources:

- **AWS Bedrock Runtime**: For invoking Claude models to generate and format
  documentation
- **IAM Permissions**: Required for Bedrock API access (not created by this
  project)

No infrastructure is deployed - this is a client-side tool that calls AWS
Bedrock services.

## Prerequisites and Requirements

### System Dependencies

- **Python 3.7+**: Required to run the Python scripts
- **AWS Account**: With Bedrock access in the configured region

### Python Dependencies

Since no `requirements.txt` file is present in the project, the scripts use
only Python standard library modules and boto3 (which should be installed
separately):

```bash
pip install boto3
```

### AWS Permissions

Your AWS credentials must have the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## Configuration

### config.json

The main configuration file defines AWS account settings and Bedrock
parameters:

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

Configuration parameters:

- `account_id`: AWS account ID for reference
- `region`: AWS region where Bedrock is available  
- `max_tokens`: Maximum tokens for content generation
- `max_tokens_reasoning`: Maximum tokens for Claude's reasoning process
- `model_id`: Specific Claude model version to use

## Usage Instructions

### Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd bedrock-documentation-generator
   ```

2. Install Python dependencies:

   ```bash
   pip install boto3
   ```

3. Configure AWS credentials using one of these methods:

   ```bash
   # Using AWS credentials file
   aws configure
   
   # Or using environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Generating README Files

Use the `readme.py` script to generate or check README files:

#### Check if README needs updating:

```bash
python scripts/readme.py \
  --check \
  --project-dir /path/to/your/project \
  --aws-region us-east-1 \
  --output-file result.txt \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000
```

#### Generate/update README:

```bash
python scripts/readme.py \
  --update \
  --project-dir /path/to/your/project \
  --aws-region us-east-1 \
  --output-file result.txt \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000
```

### Formatting Existing Markdown

Use `format_claude_md.py` to format existing CLAUDE.md files:

```bash
python format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt_template.txt
```

## Architecture Overview

### Component Interaction

1. **Configuration Loading**: Scripts read `config.json` for AWS and Bedrock
   settings
2. **File Analysis**: The system scans project directories for Python, JSON,
   YAML, and text files
3. **Content Processing**: Project files are combined and sent to Bedrock
   for analysis
4. **AI Generation**: Claude models generate documentation based on code
   analysis
5. **Output Formatting**: Generated content is formatted to comply with
   markdownlint rules

### Authentication Flow

The scripts use standard AWS SDK authentication:

1. **Credential Resolution**: boto3 automatically finds AWS credentials from
   environment, credentials file, or IAM roles
2. **Bedrock Client**: Creates a Bedrock Runtime client for the specified
   region
3. **API Calls**: Makes authenticated requests to Bedrock's Converse API
4. **Response Processing**: Extracts text content from Bedrock responses

### Data Flow

```
Project Files → File Scanner → Content Combiner → Bedrock API → 
Claude Model → Response Parser → Markdown Formatter → Output File
```

## Security Considerations

### AWS Credentials

- **Never commit** AWS credentials to version control
- Use IAM roles when running on EC2 or other AWS services
- Apply principle of least privilege for Bedrock permissions
- Rotate access keys regularly

### API Usage

- **Rate Limiting**: Scripts implement exponential backoff to handle
  throttling
- **Cost Management**: Monitor Bedrock usage as API calls incur charges
- **Content Security**: Be aware that project code is sent to AWS Bedrock
  for processing

### Data Privacy

- Project files are sent to AWS Bedrock for analysis
- Ensure compliance with your organization's data handling policies
- Consider using AWS PrivateLink for enhanced network security

## Troubleshooting

### Common Issues

#### Bedrock Access Denied

```
Error: AccessDeniedException: User is not authorized to perform bedrock:InvokeModel
```

**Solution**: Ensure your AWS credentials have Bedrock permissions and the
model is available in your region.

#### Throttling Errors

```
Warning: Bedrock throttled, retrying in 2.50s (attempt 1/5)
```

**Solution**: The scripts automatically retry with exponential backoff.
Consider reducing request frequency if throttling persists.

#### File Not Found Errors

```
Error: CLAUDE.md not found
```

**Solution**: Ensure the target markdown file exists before running
formatting scripts.

#### Invalid JSON Response

```
Warning: Failed to parse JSON response from Bedrock
```

**Solution**: This is handled gracefully with fallback parsing. Check
Bedrock model configuration if it occurs frequently.

### Debug Logging

All scripts log to stderr with informative messages. Increase verbosity by
modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Model Availability

Verify that the specified Claude model is available in your AWS region:

- Check AWS Bedrock console for model availability
- Ensure model access has been requested and approved
- Verify the model ID format matches AWS specifications
