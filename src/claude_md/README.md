# Claude Markdown Formatter

A Python tool that uses AWS Bedrock's Claude model to automatically format Markdown files to comply with markdownlint rules, specifically focusing on line length constraints.

## Features

- **Automated Line Breaking**: Breaks lines over 80 characters at natural boundaries
- **Smart Heading Handling**: Shortens long headings and moves excess text to paragraphs
- **URL Formatting**: Uses backslash continuation for long URLs
- **AWS Bedrock Integration**: Leverages Claude's language understanding for intelligent formatting
- **Retry Logic**: Built-in exponential backoff for API throttling
- **Extended Reasoning**: Supports Claude's reasoning capabilities for better formatting decisions

## Prerequisites

- Python 3.6+
- AWS CLI configured with appropriate credentials
- Access to AWS Bedrock Claude models
- `boto3` library installed

## Installation

1. Clone this repository
2. Install required dependencies:
   ```bash
   pip install boto3
   ```
3. Configure AWS credentials with Bedrock access

## Configuration

The tool uses a `config.json` file for AWS and Bedrock settings:

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

## Usage

The script formats a file named `CLAUDE.md` in the current directory:

```bash
python format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md
```

### Command Line Arguments

- `--aws-region`: AWS region for Bedrock service
- `--bedrock-model-id`: Specific Claude model ID to use
- `--max-tokens-generation`: Maximum tokens for content generation
- `--max-tokens-reasoning`: Maximum tokens for extended reasoning
- `--prompt-file`: Path to the prompt template file

## Formatting Rules

The tool applies the following rules to lines over 80 characters:

1. **Long headings**: Shortens the heading and moves remaining text to the first paragraph below
2. **Long URLs**: Breaks with backslash continuation (\)
3. **Long text**: Breaks at natural word boundaries
4. **Ordered lists**: Numbers all items as "1." for consistent formatting

### Example Transformation

**Before:**
```markdown
### CRITICAL: When troubleshooting failed GitHub Actions workflows, ALWAYS check logs first
```

**After:**
```markdown
### CRITICAL: Always check logs first

When troubleshooting failed GitHub Actions workflows...
```

## Files

- `format_claude_md.py`: Main formatting script
- `config.json`: AWS and Bedrock configuration
- `prompt.md`: Template for the formatting prompt sent to Claude
- `CLAUDE.md`: Target file to be formatted (must exist)

## Error Handling

The script includes comprehensive error handling for:

- Missing `CLAUDE.md` file
- AWS Bedrock throttling (with exponential backoff)
- Invalid API responses
- Network connectivity issues

## Logging

The tool provides detailed logging to stderr, including:

- Retry attempts and wait times
- Token usage information
- Content block analysis
- Success/failure notifications

## Contributing

When modifying the prompt template in `prompt.md`, ensure the `{current_content}` placeholder remains intact for proper content substitution.
