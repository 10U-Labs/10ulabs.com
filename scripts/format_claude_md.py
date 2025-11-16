#!/usr/bin/env python3
import argparse
import json
import logging
import os
import random
import sys
import time
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def load_config():
    config_path = os.path.join('src', 'claude_md', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

def call_bedrock_with_retry(bedrock_client, bedrock_config: dict, messages: list, max_retries: int = 5) -> dict:
    initial_jitter = random.uniform(5, 30)
    logging.info("Waiting %.2fs before Bedrock call to avoid thundering herd", initial_jitter)
    time.sleep(initial_jitter)

    for attempt in range(1, max_retries + 1):
        try:
            response = bedrock_client.converse(
                modelId=bedrock_config['model_id'],
                messages=messages,
                inferenceConfig={'maxTokens': bedrock_config['max_tokens']}
            )
            logging.info("Bedrock call succeeded on attempt %d", attempt)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries:
                    logging.error("Bedrock throttled after %d attempts", max_retries)
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.warning("Bedrock throttled, retrying in %.2fs (attempt %d/%d)",
                               wait_time, attempt, max_retries)
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError("Bedrock retry loop exited unexpectedly")

def format_claude_md(bedrock_client, current_content: str, bedrock_config: dict) -> str:
    prompt = f"""You are a technical documentation expert specializing in markdown formatting. Your task is to reformat the following CLAUDE.md file to comply with ALL markdownlint rules while preserving 100% of the content and meaning.

<current_claude_md>
{current_content}
</current_claude_md>

CRITICAL REQUIREMENTS:

1. PRESERVE ALL CONTENT:
   - Every single word, instruction, code example, and URL must be preserved
   - Do NOT remove, summarize, or rephrase ANY content
   - Do NOT add new content or explanations
   - Only change formatting to comply with markdownlint

2. FIX THESE SPECIFIC MARKDOWNLINT ISSUES:
   - MD013 (line-length): Break long lines to be under 80 characters
     * For prose: Break at natural sentence boundaries or use word wrapping
     * For code blocks: Already exempt from line-length, no change needed
     * For URLs: Wrap in angle brackets if not in code blocks
   - MD036 (no-emphasis-as-heading): Convert bold emphasis to proper headings
     * Example: **CRITICAL: FOO** becomes ### CRITICAL: FOO
     * Maintain appropriate heading levels (##, ###, ####)

3. FORMATTING RULES (markdownlint compliance):
   - Keep all lines under 80 characters (except code blocks and tables)
   - Always add blank lines before and after lists
   - Always add blank lines before and after code blocks
   - Indent code blocks with 3 spaces when inside ordered/unordered lists
   - Use proper heading levels (# ## ### ####), never use bold text as headings
   - Add language specifiers to all code blocks (```bash, ```python, etc.)
   - Wrap bare URLs in angle brackets (<https://example.com>)
   - End file with exactly one newline character
   - Use proper table formatting

VERIFICATION CHECKLIST (must verify before outputting):
- [ ] All original content preserved (every word, URL, example)
- [ ] All lines under 80 characters (except code blocks/tables)
- [ ] No bold text used as headings (all **CRITICAL:** converted to ###)
- [ ] Blank lines before/after lists
- [ ] Blank lines before/after code blocks
- [ ] Code blocks have language specifiers
- [ ] Bare URLs wrapped in angle brackets
- [ ] File ends with exactly one newline

Output ONLY the reformatted CLAUDE.md content. Do not include any preamble, explanation, or the checklist itself."""

    try:
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        formatted_content = response['output']['message']['content'][0]['text']

        if not formatted_content.endswith('\n'):
            formatted_content += '\n'
            logging.info("Added missing trailing newline to CLAUDE.md")

        logging.info("Successfully formatted CLAUDE.md with Bedrock")
        return formatted_content
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to format CLAUDE.md with Bedrock: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Format CLAUDE.md to comply with markdownlint rules using Bedrock')
    parser.add_argument('--aws-region', required=True, help='AWS region for Bedrock')
    args = parser.parse_args()

    config = load_config()

    try:
        with open('CLAUDE.md', 'r', encoding='utf-8') as f:
            current_content = f.read()
    except FileNotFoundError:
        logging.error("CLAUDE.md not found")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    bedrock_config = {
        'model_id': config.get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0'),
        'max_tokens': int(config.get('bedrock', {}).get('max_tokens', 16000))
    }

    formatted_content = format_claude_md(bedrock_client, current_content, bedrock_config)

    with open('CLAUDE.md', 'w', encoding='utf-8') as f:
        f.write(formatted_content)

    logging.info("CLAUDE.md formatted successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()
