#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import boto3

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def read_source_files() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_files = {}

    files_to_read = [
        'auth_between_aws_and_github.py'
    ]

    for file_path in files_to_read:
        full_path = os.path.join(script_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source_files[file_path] = f.read()
        except IOError as e:
            logging.error("Failed to read %s: %s", file_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in source_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_should_be_updated(bedrock_client, source_code: str, current_readme: str, model_id: str, max_tokens: int) -> bool:
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing - should be updated")
        return True

    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file is current and accurate for the given AWS-GitHub authentication infrastructure code.

<source_code>
{source_code}
</source_code>

<current_readme>
{current_readme}
</current_readme>

Check if the README has ANY issues, including but not limited to:
1. Title doesn't match actual infrastructure name
2. Inconsistent or outdated terminology throughout the document
3. Inaccurately describes the infrastructure components (OIDC provider, IAM role, Secrets Manager, trust policies)
4. Missing or incorrect documentation of authentication flow (OIDC vs direct credentials)
5. Incorrect usage instructions or command examples
6. Missing key resources created (OIDC provider, GitHubActionsRole, GitHub PAT secret)
7. Outdated command examples or file paths
8. Missing or incorrect prerequisites (Python, AWS credentials, GitHub PAT)
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
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following Python script that manages AWS-GitHub authentication infrastructure using OIDC.

<source_code>
{source_code}
</source_code>

Create a professional README that includes:
1. Title and overview of what this infrastructure does
2. Purpose and key features (OIDC-based authentication for GitHub Actions)
3. Resources created:
   - AWS IAM OIDC Identity Provider for GitHub
   - IAM Role (GitHubActionsRole) with trust policy for specific GitHub org/repo
   - IAM policies attached to the role (AdministratorAccess, SecretsManagerReadWrite)
   - AWS Secrets Manager secret containing GitHub PAT and metadata
4. Prerequisites and requirements
5. Configuration details (config.json structure)
6. Usage instructions:
   - Running the create command
   - How GitHub Actions workflows use OIDC to assume the role
7. Architecture overview:
   - How OIDC authentication works between GitHub Actions and AWS
   - Trust policy configuration
   - Credential flow (OIDC vs direct AWS credentials for bootstrap)
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
   - [ ] Prerequisites match actual dependencies (check requirements.txt)
   - [ ] Correct: boto3, Python 3.11+, AWS credentials, GitHub PAT
   - [ ] Resource descriptions match implementation (OIDC provider, IAM role, policies, secret)
   - [ ] Authentication flow accurately described (OIDC-based GitHub Actions authentication)
   - [ ] Configuration examples match config.json structure
   - [ ] Trust policy format matches implementation

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

def main():
    parser = argparse.ArgumentParser(description='Generate or check README for auth infrastructure')
    parser.add_argument('--check', action='store_true', help='Check if README is current')
    parser.add_argument('--update', action='store_true', help='Update README')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--output-file', help='Output file for check result (for GitHub Actions)')
    parser.add_argument('--bedrock-model-id', help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-check', type=int, help='Max tokens for README check')
    parser.add_argument('--max-tokens-generate', type=int, help='Max tokens for README generation')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

    bedrock_model_id = args.bedrock_model_id or config.get('aws', {}).get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    max_tokens_check = int(args.max_tokens_check or config.get('aws', {}).get('bedrock', {}).get('max_tokens_check', 200))
    max_tokens_generate = int(args.max_tokens_generate or config.get('aws', {}).get('bedrock', {}).get('max_tokens_generate', 16000))

    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    source_code = read_source_files()
    readme_path = os.path.join(script_dir, 'README.md')

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
