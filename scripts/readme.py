#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import glob
import boto3

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def find_source_files(project_dir: str) -> list:
    source_files = []

    patterns = [
        os.path.join(project_dir, '*.py'),
        os.path.join(project_dir, 'lambda', '*.py'),
        os.path.join(project_dir, 'lambda', '*', '*.py'),
    ]

    for pattern in patterns:
        source_files.extend(glob.glob(pattern))

    excluded_names = ['readme.py', 'conftest.py', 'test_']
    source_files = [
        f for f in source_files
        if not any(excluded in os.path.basename(f) for excluded in excluded_names)
    ]

    return sorted(source_files)

def read_source_files(project_dir: str) -> str:
    source_files_paths = find_source_files(project_dir)

    if not source_files_paths:
        logging.warning("No source files found in %s", project_dir)
        return ""

    source_files = {}
    for full_path in source_files_paths:
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                rel_path = os.path.relpath(full_path, project_dir)
                source_files[rel_path] = f.read()
        except IOError as e:
            logging.error("Failed to read %s: %s", full_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in source_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_should_be_updated(bedrock_client, source_code: str, current_readme: str, model_id: str, max_tokens: int) -> bool:
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing - should be updated")
        return True

    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file is current and accurate for the given infrastructure code.

<source_code>
{source_code}
</source_code>

<current_readme>
{current_readme}
</current_readme>

Check if the README has ANY issues, including but not limited to:
1. Title doesn't match actual infrastructure name
2. Inconsistent or outdated terminology throughout the document
3. Inaccurately describes the infrastructure components
4. Missing or incorrect documentation of authentication flow
5. Incorrect usage instructions or command examples
6. Missing key resources created
7. Outdated command examples or file paths
8. Missing or incorrect prerequisites
9. Contains a "License" section (MAJOR ERROR - repository has LICENSE.md, README must not duplicate licensing)
10. Any other inaccuracies, inconsistencies, or outdated information

Respond with ONLY a JSON object in this exact format:
{{
  "readme_should_be_updated": true,
  "reasoning": "Explain your thought process and what issues you found, if any"
}}

or

{{
  "readme_should_be_updated": false,
  "reasoning": "Explain your thought process and confirm the README is current"
}}

Do not include any other text or formatting outside the JSON object."""

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }],
            inferenceConfig={
                'maxTokens': max_tokens
            }
        )

        answer_text = response['output']['message']['content'][0]['text'].strip()
        try:
            result = json.loads(answer_text)
            should_be_updated = bool(result.get('readme_should_be_updated', False))
            reasoning = result.get('reasoning', 'No reasoning provided')
            logging.info("Bedrock reasoning: %s", reasoning)
            status = 'be updated' if should_be_updated else 'not be updated'
            logging.info("Bedrock assessment: README should %s", status)
            return should_be_updated
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse JSON response from Bedrock: %s", e)
            logging.warning("Raw response: %s", answer_text)
            should_be_updated = answer_text.lower().startswith('true')
            status = 'be updated (fallback)' if should_be_updated else 'not be updated (fallback)'
            logging.info("Bedrock assessment: README should %s", status)
            return should_be_updated
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to check README with Bedrock: %s", e)
        sys.exit(1)

def generate_readme(bedrock_client, source_code: str, model_id: str, max_tokens: int) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following infrastructure code.

<source_code>
{source_code}
</source_code>

Create a professional README that includes:
1. Title and overview of what this infrastructure does
2. Purpose and key features
3. Resources created (analyze the code to identify all AWS resources)
4. Prerequisites and requirements (check dependencies from requirements.txt or imports)
5. Configuration details (config.json structure if present)
6. Usage instructions:
   - Installation steps
   - Running the infrastructure (CDK deploy, scripts, etc.)
   - How to use the deployed resources
7. Architecture overview:
   - How the components interact
   - Authentication and authorization flows
   - Data flows and integrations
8. Security considerations
9. Troubleshooting tips

IMPORTANT: Do NOT include a "License" section. The repository already has a LICENSE.md file, so the README must not duplicate licensing information.

Format the README in clean, professional markdown that complies with all markdownlint rules:
- Keep all lines under 80 characters
- Always add blank lines before and after lists
- Always add blank lines before and after code blocks
- Indent code blocks with 3 spaces when inside ordered/unordered lists
- Use proper heading levels (# ## ### ####), never use bold text as headings
- Add language specifiers to all code blocks (```bash, ```python, ```json, etc.)
- Wrap bare URLs in angle brackets (<https://example.com>)
- End file with exactly one newline character
- Use proper table formatting with spaces around pipes (| Column 1 | Column 2 |)

CRITICAL INSTRUCTIONS:
1. Generate the README content first
2. Before outputting, verify EACH requirement using this checklist:

   FACTUAL ACCURACY (verify against source code):
   - [ ] Prerequisites match actual dependencies
   - [ ] Resource descriptions match implementation
   - [ ] Configuration examples match actual config structure
   - [ ] Usage instructions are accurate and complete

   FORMATTING (markdownlint compliance):
   - [ ] All lines under 80 characters
   - [ ] Blank lines before/after lists
   - [ ] Blank lines before/after code blocks
   - [ ] Code blocks indented with 3 spaces when inside lists
   - [ ] All headings use # syntax (not bold)
   - [ ] All code blocks have language specifiers
   - [ ] All bare URLs wrapped in angle brackets
   - [ ] File ends with exactly one newline
   - [ ] No License section included

3. If any check fails, fix the issue before outputting
4. Output ONLY the final README content (no checklist, no explanation)

Be specific about what each resource does and why it exists. Use code blocks for examples.
Generate ONLY the README content, starting with the title. Do not include any preamble or explanation."""

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }],
            inferenceConfig={
                'maxTokens': max_tokens
            }
        )

        readme_content = response['output']['message']['content'][0]['text']

        if not readme_content.endswith('\n'):
            readme_content += '\n'
            logging.info("Added missing trailing newline to README")

        logging.info("Successfully generated README with Bedrock")
        return readme_content
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to generate README with Bedrock: %s", e)
        sys.exit(1)

def load_config(project_dir: str):
    config_path = os.path.join(project_dir, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Generate or check README for infrastructure projects')
    parser.add_argument('--check', action='store_true', help='Check if README is current')
    parser.add_argument('--update', action='store_true', help='Update README')
    parser.add_argument('--project-dir', required=True, help='Project directory path')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--output-file', help='Output file for check result (for GitHub Actions)')
    parser.add_argument('--bedrock-model-id', help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-check', type=int, help='Max tokens for README check')
    parser.add_argument('--max-tokens-generate', type=int, help='Max tokens for README generation')
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        logging.error("Project directory does not exist: %s", project_dir)
        sys.exit(1)

    config = load_config(project_dir)

    bedrock_model_id = args.bedrock_model_id or config.get('aws', {}).get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    max_tokens_check = int(args.max_tokens_check or config.get('aws', {}).get('bedrock', {}).get('max_tokens_check', 200))
    max_tokens_generate = int(args.max_tokens_generate or config.get('aws', {}).get('bedrock', {}).get('max_tokens_generate', 16000))

    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    source_code = read_source_files(project_dir)
    readme_path = os.path.join(project_dir, 'README.md')

    if args.check:
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except FileNotFoundError:
            current_readme = ""

        should_be_updated = check_readme_should_be_updated(bedrock_client, source_code, current_readme, bedrock_model_id, max_tokens_check)

        if args.output_file:
            with open(args.output_file, 'a', encoding='utf-8') as f:
                f.write(f"readme_should_be_updated={'true' if should_be_updated else 'false'}\n")

        sys.exit(0)

    elif args.update:
        new_readme = generate_readme(bedrock_client, source_code, bedrock_model_id, max_tokens_generate)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)

        logging.info("README updated at %s", readme_path)
        sys.exit(0)

if __name__ == '__main__':
    main()
