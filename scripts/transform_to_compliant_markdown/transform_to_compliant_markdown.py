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

def format_claude_md(bedrock_client, current_content: str, bedrock_config: dict, prompt_file: str, markdownlint_errors: str = '') -> str:
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        current_content=current_content,
        markdownlint_errors=markdownlint_errors
    )

    try:
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        content_blocks = response['output']['message']['content']

        block_keys = [list(block.keys()) for block in content_blocks]
        logging.info("Response contains %d content blocks with keys: %s", len(content_blocks), block_keys)

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
    parser.add_argument('--prompt-file', required=True, help='Path to prompt template file')
    parser.add_argument('--markdownlint-errors', default='', help='JSON output from markdownlint-cli showing errors to fix')
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

    formatted_content = format_claude_md(bedrock_client, current_content, bedrock_config, args.prompt_file, args.markdownlint_errors)

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
