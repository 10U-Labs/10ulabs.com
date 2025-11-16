#!/usr/bin/env python3
import argparse
import logging
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

def call_bedrock_with_retry(bedrock_client, bedrock_config: dict, messages: list, max_retries: int = 5) -> dict:
    initial_jitter = random.randint(5, 30)
    logging.info("Waiting %ds before Bedrock call to avoid thundering herd", initial_jitter)
    time.sleep(initial_jitter)

    for attempt in range(1, max_retries + 1):
        try:
            kwargs = {
                'modelId': bedrock_config['model_id'],
                'messages': messages,
                'inferenceConfig': {'maxTokens': bedrock_config['max_tokens']}
            }

            if 'max_tokens_reasoning' in bedrock_config:
                kwargs['additionalModelRequestFields'] = {
                    'reasoning_config': {
                        'type': 'enabled',
                        'budget_tokens': bedrock_config['max_tokens_reasoning']
                    }
                }
                logging.info("Extended thinking enabled with %d reasoning tokens",
                           bedrock_config['max_tokens_reasoning'])

            response = bedrock_client.converse(**kwargs)
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

1. CONTENT PRESERVATION:
   - Every single word, instruction, code example, and URL must be preserved
   - Do NOT remove, summarize, or rephrase ANY content
   - Do NOT add new content or explanations
   - You MUST make formatting changes to comply with markdownlint - this is REQUIRED

2. FORMATTING CHANGES YOU MUST MAKE:
   - MD001: Heading levels increment by one (no skipping from # to ###)
   - MD003: Heading style consistent (ATX style with #)
   - MD004: Unordered list style consistent
   - MD005: List item indentation consistent
   - MD007: Unordered list indentation (2 spaces per level)
   - MD009: No trailing spaces
   - MD010: No hard tabs (use spaces)
   - MD011: Reversed link syntax
   - MD012: No multiple consecutive blank lines
   - MD013: Line length max 80 characters - BREAK ALL LONG LINES including headings and code blocks
   - MD014: Dollar signs in shell commands only when showing output
   - MD018: Space after hash in headings (# Heading not #Heading)
   - MD019: No multiple spaces after hash in headings
   - MD022: Headings surrounded by blank lines
   - MD023: Headings must start at beginning of line
   - MD024: No multiple headings with same content
   - MD025: Single H1 heading only
   - MD026: No trailing punctuation in headings
   - MD027: No multiple spaces after blockquote symbol
   - MD028: No blank lines inside blockquote
   - MD029: Ordered list item prefix (consistent numbering)
   - MD030: Spaces after list markers
   - MD031: Fenced code blocks surrounded by blank lines
   - MD032: Lists surrounded by blank lines
   - MD033: No inline HTML (use markdown)
   - MD034: Bare URLs wrapped in angle brackets
   - MD035: Horizontal rule style consistent
   - MD036: No emphasis used instead of heading
   - MD037: No spaces inside emphasis markers
   - MD038: No spaces inside code span elements
   - MD039: No spaces inside link text
   - MD040: Fenced code blocks have language specified
   - MD041: First line in file should be top-level heading
   - MD042: No empty links
   - MD043: Required heading structure
   - MD044: Proper names capitalized correctly
   - MD045: Images have alt text
   - MD046: Code block style consistent (fenced)
   - MD047: File ends with single newline
   - MD048: Code fence style consistent
   - MD049: Emphasis style consistent
   - MD050: Strong style consistent

3. REQUIRED CHANGES FOR COMMON VIOLATIONS:

   MD013 (long lines) - BREAK ALL LINES over 80 chars - NO EXCEPTIONS:
   - Long headings: Shorten the heading text or move details to first paragraph
     Before: "### CRITICAL: When troubleshooting failed workflows, ALWAYS check logs first"
     After: "### CRITICAL: Always check logs first\n\nWhen troubleshooting failed workflows..."

   - Long URLs in bash code: Use backslash continuation before line break
     Before: curl -s "https://api.github.com/repos/owner/repo/very/long/path"
     After: curl -s \\\n  "https://api.github.com/repos/owner/repo/very/long/path"

   - MD029 (list numbering): Use 1/1/1/1 style - ALL ordered list items numbered "1."
   - MD036 (bold as headings): Convert bold emphasis to proper heading levels
   - MD034 (bare URLs): Wrap in angle brackets unless in code blocks
   - MD040 (code blocks): Add language identifier (bash, python, json, etc.)
   - MD032 (list spacing): Ensure blank lines before and after lists

VERIFICATION CHECKLIST (verify ALL before outputting):
- [ ] All original content preserved (every word, URL, example)
- [ ] ALL lines under 80 characters - NO EXCEPTIONS
- [ ] ALL ordered list items numbered "1." (not 1, 2, 3, 4)
- [ ] Headings have proper levels and spacing
- [ ] Lists have blank lines before/after
- [ ] Code blocks have language and blank lines
- [ ] No bold emphasis used as headings
- [ ] File ends with single newline

Output ONLY the reformatted CLAUDE.md content. Do not include any preamble, explanation, or checklist."""

    try:
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        content_blocks = response['output']['message']['content']

        block_keys = [list(block.keys()) for block in content_blocks]
        logging.info("Response contains %d content blocks with keys: %s", len(content_blocks), block_keys)

        reasoning_blocks = [block for block in content_blocks if 'reasoningContent' in block]
        if reasoning_blocks:
            reasoning_content = reasoning_blocks[0]['reasoningContent']
            if isinstance(reasoning_content, str):
                logging.info("Extended thinking reasoning (first 500 chars): %s", reasoning_content[:500])
            else:
                logging.info("Extended thinking reasoning structure: %s", reasoning_content)

        text_blocks = [block for block in content_blocks if 'text' in block]

        if not text_blocks:
            logging.error("No text blocks found in Bedrock response")
            logging.error("Available block keys: %s", block_keys)
            sys.exit(1)

        formatted_content = text_blocks[0]['text']

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
    parser.add_argument('--bedrock-model-id', required=True, help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-generation', type=int, required=True, help='Max tokens for formatting')
    parser.add_argument('--max-tokens-reasoning', type=int, required=True, help='Max tokens for extended thinking reasoning')
    args = parser.parse_args()

    try:
        with open('CLAUDE.md', 'r', encoding='utf-8') as f:
            current_content = f.read()
    except FileNotFoundError:
        logging.error("CLAUDE.md not found")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    bedrock_config = {
        'model_id': args.bedrock_model_id,
        'max_tokens': args.max_tokens_generation,
        'max_tokens_reasoning': args.max_tokens_reasoning
    }

    formatted_content = format_claude_md(bedrock_client, current_content, bedrock_config)

    if formatted_content == current_content:
        logging.warning("Bedrock returned identical content - no formatting changes made")
    else:
        logging.info("Bedrock made formatting changes")

    with open('CLAUDE.md', 'w', encoding='utf-8') as f:
        f.write(formatted_content)

    logging.info("CLAUDE.md formatted successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()
