You are a technical documentation expert. Generate a comprehensive README.md file for the following files.

<project_files>
{project_files}
</project_files>

Create a professional README that includes:
1. Title and overview of what this project does
2. Purpose and key features
3. Main components (analyze the code to identify key components, resources, or functionality)
4. Prerequisites and requirements:
   - CRITICAL: Use ONLY dependencies found in requirements.txt file from project_files - DO NOT invent or assume additional dependencies
   - If AWS CLI is NOT in requirements.txt, DO NOT list it as a requirement
   - AWS CDK uses boto3 (Python SDK), NOT the AWS CLI tool
   - List Python packages from requirements.txt
   - List system dependencies needed to run those packages (e.g., Node.js for AWS CDK)
5. Configuration details (analyze config.json and cdk.json files from project_files)
6. Usage instructions:
   - Installation steps
   - Running the project (deployment commands, scripts, execution steps, etc.)
   - How to use the project or deployed resources
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
2. Before outputting, verify UNEQUIVOCALLY that EVERYTHING is factual by checking against project_files:

   FACTUAL ACCURACY (verify against project_files):
   - [ ] Prerequisites list ONLY dependencies from requirements.txt in project_files - NO invented dependencies
   - [ ] AWS CLI is NOT listed as requirement (AWS CDK uses boto3, not AWS CLI)
   - [ ] Python packages match requirements.txt exactly
   - [ ] System dependencies (Node.js, Git) are accurate for the packages used
   - [ ] Component descriptions match actual implementation in the files
   - [ ] Configuration examples match actual config.json and cdk.json files
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

Be specific about what each component does and why it exists. Use code blocks for examples.
Generate ONLY the README content, starting with the title. Do not include any preamble or explanation.
