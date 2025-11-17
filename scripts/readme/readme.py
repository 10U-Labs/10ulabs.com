#!/usr/bin/env python3
import argparse
import json
import logging
import os
import random
import sys
import time
import glob
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def split_text_by_words(text: str, max_length: int = 1000) -> list:
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    words = text.split()
    for word in words:
        if len(current_chunk) + len(word) + 1 <= max_length:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def call_bedrock_with_retry(bedrock_client, bedrock_config: dict, messages: list, max_retries: int = 5) -> dict:
    initial_jitter = random.randint(5, 30)
    logging.info("Waiting %ds before Bedrock call to avoid thundering herd", initial_jitter)
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

def find_all_project_files(project_dir: str) -> list:
    all_files = []

    patterns = [
        os.path.join(project_dir, '*.py'),
        os.path.join(project_dir, '*.json'),
        os.path.join(project_dir, '*.txt'),
        os.path.join(project_dir, '*.md'),
        os.path.join(project_dir, '*.yaml'),
        os.path.join(project_dir, '*.yml'),
        os.path.join(project_dir, 'lambda', '*.py'),
        os.path.join(project_dir, 'lambda', '*', '*.py'),
    ]

    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    excluded_names = ['readme.py', 'conftest.py', 'test_', 'README.md']
    all_files = [
        f for f in all_files
        if not any(excluded in os.path.basename(f) for excluded in excluded_names)
    ]

    return sorted(all_files)

def read_all_project_files(project_dir: str) -> str:
    all_file_paths = find_all_project_files(project_dir)

    repo_root = project_dir
    while repo_root and repo_root != '/':
        if os.path.exists(os.path.join(repo_root, 'scripts', 'readme.py')):
            break
        repo_root = os.path.dirname(repo_root)

    if os.path.exists(os.path.join(repo_root, 'scripts', 'readme.py')):
        all_file_paths.append(os.path.join(repo_root, 'scripts', 'readme.py'))

    if not all_file_paths:
        logging.warning("No files found in %s", project_dir)
        return ""

    all_files = {}
    for full_path in all_file_paths:
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if 'scripts/readme.py' in full_path:
                    rel_path = 'scripts/readme.py'
                else:
                    rel_path = os.path.relpath(full_path, project_dir)
                all_files[rel_path] = f.read()
        except IOError as e:
            logging.error("Failed to read %s: %s", full_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in all_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_should_be_updated(bedrock_client, project_files: str, current_readme: str, bedrock_config: dict, prompt_file: str) -> bool:
    result = False
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing - should be updated")
        result = True
    else:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().format(project_files=project_files, current_readme=current_readme)
        try:
            response = call_bedrock_with_retry(bedrock_client, bedrock_config, [{'role': 'user', 'content': [{'text': prompt}]}])
            answer_text = response['output']['message']['content'][0]['text'].strip()
            try:
                parsed = json.loads(answer_text)
                result = bool(parsed.get('readme_should_be_updated', False))
                for i, chunk in enumerate(split_text_by_words(parsed.get('reasoning', 'No reasoning provided'), max_length=1000), 1):
                    logging.info("Bedrock reasoning (part %d): %s", i, chunk)
                logging.info("Bedrock assessment: README should %s", 'be updated' if result else 'not be updated')
            except json.JSONDecodeError as e:
                logging.warning("Failed to parse JSON response from Bedrock: %s", e)
                logging.warning("Raw response: %s", answer_text)
                result = answer_text.lower().startswith('true')
                logging.info("Bedrock assessment: README should %s", 'be updated (fallback)' if result else 'not be updated (fallback)')
        except (KeyError, IndexError, TypeError) as e:
            logging.error("Failed to check README with Bedrock: %s", e)
            sys.exit(1)
    return result

def generate_readme(bedrock_client, project_files: str, bedrock_config: dict, prompt_file: str) -> str:
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template.format(project_files=project_files)

    try:
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        readme_content = response['output']['message']['content'][0]['text']

        if not readme_content.endswith('\n'):
            readme_content += '\n'
            logging.info("Added missing trailing newline to README")

        logging.info("Successfully generated README with Bedrock")
        return readme_content
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to generate README with Bedrock: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Generate or check README for infrastructure projects')
    parser.add_argument('--check', action='store_true', help='Check if README is current')
    parser.add_argument('--update', action='store_true', help='Update README')
    parser.add_argument('--project-dir', required=True, help='Project directory path')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--output-file', required=True, help='Output file for check result (for GitHub Actions)')
    parser.add_argument('--bedrock-model-id', required=True, help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-reasoning', type=int, required=True, help='Max tokens for extended thinking reasoning')
    parser.add_argument('--max-tokens-generation', type=int, required=True, help='Max tokens for README generation')
    parser.add_argument('--prompt-check', required=True, help='Path to check prompt template file')
    parser.add_argument('--prompt-update', required=True, help='Path to update prompt template file')
    args = parser.parse_args()
    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        logging.error("Project directory does not exist: %s", project_dir)
        sys.exit(1)
    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)
    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    project_files = read_all_project_files(project_dir)
    if args.check:
        try:
            with open(os.path.join(project_dir, 'README.md'), 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except FileNotFoundError:
            current_readme = ""
        bedrock_config = {
            'model_id': args.bedrock_model_id,
            'max_tokens': args.max_tokens_reasoning
        }
        should_be_updated = check_readme_should_be_updated(bedrock_client, project_files, current_readme, bedrock_config, args.prompt_check)
        result_value = 'true' if should_be_updated else 'false'
        if args.output_file:
            logging.info("Writing output to file: %s", args.output_file)
            with open(args.output_file, 'a', encoding='utf-8') as f:
                f.write(f"readme_should_be_updated={result_value}\n")
            logging.info("Successfully wrote readme_should_be_updated=%s", result_value)
        else:
            logging.warning("No output file specified, result: readme_should_be_updated=%s", result_value)
        sys.exit(0)
    elif args.update:
        bedrock_config = {
            'model_id': args.bedrock_model_id,
            'max_tokens': args.max_tokens_generation
        }
        new_readme = generate_readme(bedrock_client, project_files, bedrock_config, args.prompt_update)
        with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(new_readme)
        logging.info("README updated at %s", os.path.join(project_dir, 'README.md'))
        sys.exit(0)

if __name__ == '__main__':
    main()
