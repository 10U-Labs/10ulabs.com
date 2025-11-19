# Markdown Compliance Transformer

A Python tool that uses AWS Bedrock (Claude) to automatically fix markdownlint violations in markdown files while preserving all content exactly.

## Features

- **AI-Powered Formatting**: Uses Claude Sonnet 4 via AWS Bedrock to intelligently fix markdown violations
- **Content Preservation**: Maintains exact content while fixing formatting issues
- **Robust Retry Logic**: Handles AWS throttling with exponential backoff and jitter
- **Extended Thinking**: Uses budget tokens for complex formatting decisions
- **Flexible Input**: Works with any markdown file and optional markdownlint error reports
- **Comprehensive Testing**: Includes unit, integration, and end-to-end tests

## Prerequisites

- Python 3.7+
- AWS credentials configured (via OIDC, environment variables, or AWS profiles)
- Access to AWS Bedrock service with Claude Sonnet 4 model
- Required Python packages: `boto3`

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install boto3
```

## Configuration

The tool uses `config.json` for default settings:

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

## Usage

### Basic Usage

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens 64000 \
  --budget-tokens 10000 \
  --prompt-file prompt.md
```

### With Specific Markdownlint Errors

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens 64000 \
  --budget-tokens 10000 \
  --prompt-file prompt.md \
  --markdownlint-errors '{"README.md": [{"lineNumber": 2, "ruleNames": ["MD013"], "ruleDescription": "Line length"}]}'
```

## Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--file` | Yes | Path to markdown file to format |
| `--aws-region` | Yes | AWS region for Bedrock service |
| `--bedrock-model-id` | Yes | Bedrock model ID to use |
| `--max-tokens` | Yes | Maximum tokens for model output |
| `--budget-tokens` | Yes | Budget tokens for extended thinking |
| `--prompt-file` | Yes | Path to prompt template file |
| `--markdownlint-errors` | No | JSON output from markdownlint-cli |

## How It Works

1. **Input Processing**: Reads the specified markdown file and optional markdownlint errors
2. **Prompt Generation**: Uses the template in `prompt.md` to create instructions for Claude
3. **AI Processing**: Sends the content to AWS Bedrock with retry logic and throttling protection
4. **Output Generation**: Writes the formatted content back to the original file
5. **Validation**: Ensures proper newline termination

## Supported Markdownlint Rules

The tool can fix common markdownlint violations including:

- **MD041**: Missing first-line heading
- **MD013**: Line length violations (breaks long lines)
- **MD022**: Missing blank lines around headings
- **MD012**: Multiple consecutive blank lines
- **MD009**: Trailing whitespace
- **MD047**: Single trailing newline

## Error Handling

- **Throttling**: Automatic retry with exponential backoff
- **Missing Files**: Clear error messages and proper exit codes
- **API Errors**: Comprehensive error logging and graceful failures
- **Invalid Responses**: Validates Bedrock response structure

## Testing

Run the test suite:

```bash
# Unit tests
pytest test/transform_to_compliant_markdown/test_unit.py

# Integration tests
pytest test/transform_to_compliant_markdown/test_integration.py

# End-to-end tests (requires AWS credentials)
pytest test/transform_to_compliant_markdown/test_e2e.py
```

## Project Structure

```
scripts/transform_to_compliant_markdown/
├── transform_to_compliant_markdown.py  # Main script
├── config.json                         # Configuration file
├── prompt.md                          # Claude prompt template
└── test/transform_to_compliant_markdown/
    ├── conftest.py                    # Test fixtures
    ├── test_unit.py                   # Unit tests
    ├── test_integration.py            # Integration tests
    └── test_e2e.py                    # End-to-end tests
```

## Performance Considerations

- **Jitter**: Random delays prevent thundering herd problems
- **Budget Tokens**: Extended thinking capability for complex formatting
- **Retry Logic**: Handles AWS service limits gracefully
- **Content Preservation**: Maintains original meaning while fixing format

## Troubleshooting

### AWS Credentials
Ensure AWS credentials are properly configured. The tool supports:
- OIDC authentication (recommended for CI/CD)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS profiles

### Bedrock Access
Verify access to AWS Bedrock service and the Claude Sonnet 4 model in your AWS account.

### File Permissions
Ensure the script has read/write permissions for the target markdown files.
