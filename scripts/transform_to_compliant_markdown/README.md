# Markdown Linter Formatter

An AI-powered tool that automatically fixes markdownlint violations in Markdown files using AWS Bedrock and Claude Sonnet. The tool preserves all content while ensuring compliance with markdownlint rules.

## Features

- **AI-Powered Formatting**: Uses AWS Bedrock with Claude Sonnet to intelligently fix markdownlint violations
- **Content Preservation**: Maintains all original content, meaning, and information while fixing formatting issues
- **Comprehensive Rule Support**: Handles common markdownlint violations including line length, heading formatting, trailing spaces, and more
- **Robust Error Handling**: Implements exponential backoff retry logic for AWS API throttling
- **Flexible Input**: Accepts markdownlint error output or applies general best practices
- **Configurable**: JSON configuration file for easy customization of AWS and Bedrock settings

## Prerequisites

- Python 3.6+
- AWS credentials configured (via AWS CLI, environment variables, or IAM roles)
- Access to AWS Bedrock with Claude Sonnet model permissions
- Required Python packages: `boto3`, `botocore`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install boto3 botocore
```

3. Configure AWS credentials:
```bash
aws configure
```

## Configuration

The tool uses a `config.json` file with the following structure:

```json
{
  "account_id": 781581267945,
  "region": "us-east-1",
  "bedrock": {
    "budget_tokens": 10000,
    "max_tokens": 64000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

### Configuration Options

- `account_id`: AWS account ID
- `region`: AWS region for Bedrock service
- `bedrock.budget_tokens`: Token budget for extended thinking
- `bedrock.max_tokens`: Maximum tokens for model output
- `bedrock.model_id`: Bedrock model identifier

## Usage

### Basic Usage

Format a markdown file using the default configuration:

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens 64000 \
  --budget-tokens 10000 \
  --prompt-file prompt.md
```

### With Markdownlint Errors

If you have specific markdownlint violations to fix:

```bash
# First, run markdownlint to get violations
markdownlint README.md --json > errors.json

# Then fix the violations
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens 64000 \
  --budget-tokens 10000 \
  --prompt-file prompt.md \
  --markdownlint-errors "$(cat errors.json)"
```

### Command Line Arguments

- `--file`: Path to the markdown file to format (required)
- `--aws-region`: AWS region for Bedrock (required)
- `--bedrock-model-id`: Bedrock model ID to use (required)
- `--max-tokens`: Maximum tokens for model output (required)
- `--budget-tokens`: Budget tokens for extended thinking (required)
- `--prompt-file`: Path to prompt template file (required)
- `--markdownlint-errors`: JSON output from markdownlint-cli (optional)

## How It Works

1. **Input Processing**: Reads the target markdown file and optional markdownlint error output
2. **Prompt Generation**: Creates a comprehensive prompt using the template in `prompt.md`
3. **AI Processing**: Sends the prompt to AWS Bedrock using Claude Sonnet with extended thinking enabled
4. **Retry Logic**: Implements exponential backoff for handling API throttling
5. **Output Validation**: Ensures the formatted content ends with a newline
6. **File Update**: Overwrites the original file with the formatted content

### Supported Markdownlint Rules

The tool handles common violations including:

- **MD041**: Missing first-line heading
- **MD013**: Line length violations (breaks lines at 80 characters)
- **MD022**: Missing blank lines around headings
- **MD012**: Multiple consecutive blank lines
- **MD009**: Trailing whitespace
- **MD047**: Missing single trailing newline

## Testing

The project includes comprehensive tests:

### Run Unit Tests
```bash
python -m pytest test/transform_to_compliant_markdown/test_unit.py -v
```

### Run Integration Tests
```bash
python -m pytest test/transform_to_compliant_markdown/test_integration.py -v
```

### Run End-to-End Tests (requires AWS credentials)
```bash
python -m pytest test/transform_to_compliant_markdown/test_e2e.py -v
```

### Run All Tests
```bash
python -m pytest test/transform_to_compliant_markdown/ -v
```

Note: End-to-end tests are automatically skipped if AWS credentials are not available.

## Project Structure

```
├── config.json                           # AWS and Bedrock configuration
├── prompt.md                            # Prompt template for Claude
├── transform_to_compliant_markdown.py   # Main script
└── test/transform_to_compliant_markdown/
    ├── conftest.py                      # Test fixtures
    ├── test_unit.py                     # Unit tests
    ├── test_integration.py              # Integration tests
    └── test_e2e.py                      # End-to-end tests
```

## Error Handling

The tool includes robust error handling:

- **File Not Found**: Exits with error code 1 if the target file doesn't exist
- **AWS Throttling**: Implements exponential backoff with jitter for rate limiting
- **Invalid Response**: Validates Bedrock response structure and exits gracefully on errors
- **Missing Content**: Ensures output always includes required content blocks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install pytest boto3 botocore

# Run tests
python -m pytest test/transform_to_compliant_markdown/ -v
```
