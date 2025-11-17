# Markdown Compliance Transformer

A Python script that automatically fixes markdownlint violations in Markdown files using AWS Bedrock's Claude model. The tool preserves all content while applying formatting fixes to ensure compliance with markdown linting rules.

## Features

- **AI-Powered Formatting**: Uses AWS Bedrock Claude Sonnet model for intelligent markdown formatting
- **Content Preservation**: Maintains all original content while fixing formatting issues
- **Markdownlint Integration**: Processes specific markdownlint violations or applies general best practices
- **Retry Logic**: Built-in exponential backoff and retry mechanism for API throttling
- **Extended Reasoning**: Leverages Claude's reasoning capabilities for complex formatting decisions

## Prerequisites

- Python 3.6+
- AWS credentials configured (IAM role, environment variables, or AWS CLI)
- Access to AWS Bedrock service in your region
- `boto3` Python package

## Installation

1. Clone the repository or download the script files
2. Install required dependencies:
```bash
pip install boto3
```

## Configuration

Edit `config.json` to match your AWS setup:

```json
{
  "account_id": 781581267945,
  "region": "us-east-1",
  "bedrock": {
    "max_tokens_generation": 16000,
    "max_tokens_reasoning": 4000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

## Usage

### Basic Usage

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md
```

### With Specific Markdownlint Errors

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md \
  --markdownlint-errors '{"file.md": [{"lineNumber": 2, "ruleNames": ["MD013"]}]}'
```

## Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--file` | Yes | Path to the markdown file to format |
| `--aws-region` | Yes | AWS region for Bedrock service |
| `--bedrock-model-id` | Yes | Bedrock model ID to use |
| `--max-tokens-generation` | Yes | Maximum tokens for content generation |
| `--max-tokens-reasoning` | Yes | Maximum tokens for reasoning process |
| `--prompt-file` | Yes | Path to the prompt template file |
| `--markdownlint-errors` | No | JSON string of markdownlint errors to fix |

## Files

### `transform_to_compliant_markdown.py`
Main script that processes markdown files and applies formatting fixes using AWS Bedrock.

### `config.json`
Configuration file containing AWS account details and Bedrock model settings.

### `prompt.md`
Template file containing the prompt instructions for the AI model. Includes specific rules for fixing common markdownlint violations like:
- MD041 (first-line-heading): Missing level-1 heading
- MD013 (line-length): Lines exceeding 80 characters
- MD022 (blanks-around-headings): Missing blank lines around headings
- MD012 (no-multiple-blanks): Multiple consecutive blank lines
- MD009 (no-trailing-spaces): Trailing whitespace
- MD047 (single-trailing-newline): Missing or multiple trailing newlines

## Error Handling

The script includes comprehensive error handling for:

- **File Not Found**: Exits with code 1 if the specified markdown file doesn't exist
- **AWS Throttling**: Implements exponential backoff retry logic for rate limiting
- **Invalid Bedrock Response**: Validates response structure and content blocks
- **Missing Trailing Newlines**: Automatically adds required trailing newline

## Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest test/transform_to_compliant_markdown/

# Run specific test categories
pytest test/transform_to_compliant_markdown/test_unit.py
pytest test/transform_to_compliant_markdown/test_integration.py
pytest test/transform_to_compliant_markdown/test_e2e.py
```

**Note**: End-to-end tests require valid AWS credentials and Bedrock access.

## Common Markdownlint Fixes

The tool automatically handles common violations:

- **Long Lines**: Breaks lines over 80 characters with backslash continuation
- **Missing Headings**: Adds level-1 heading as first line when required
- **Blank Line Issues**: Adds/removes blank lines around headings as needed
- **Trailing Spaces**: Removes unwanted trailing whitespace
- **File Endings**: Ensures files end with exactly one newline

## Logging

The script provides detailed logging output including:
- Retry attempts and wait times
- Bedrock response analysis
- Content change detection
- Error details and troubleshooting information

All logs are written to stderr to keep stdout clean for potential piping.
