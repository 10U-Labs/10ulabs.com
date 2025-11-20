# Development Guidelines

## Credentials and Environment

- AWS access key ID in your environment variables as AWS_ACCESS_KEY_ID
- AWS secret key in your environment variables as AWS_SECRET_ACCESS_KEY
- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY have unlimited privileges in \
  AWS
- GitHub Personal Access Token (PAT) in your environment variables as \
  GITHUB_PAT
- GITHUB_PAT has unlimited privileges in GitHub
- Do not use environment variable expansion like $GITHUB_PAT in curl \
  commands, instead obtain the value first by running 'echo $GITHUB_PAT' \
  and passing the value literally

## Code Quality Standards

- NEVER add ANY form of comment to source code
- If comments already exist in the original code, REMOVE THEM
- NEVER add inline comments (# comments)
- NEVER add docstrings ("""...""")
- NEVER disable lint checks
- If linters fail, fix the actual code
- NEVER CREATE LINTER CONFIGURATION FILES
- FUNCTIONS MUST HAVE SINGLE RETURN STATEMENT

## Testing Standards

- TESTS MUST HAVE ONLY ONE ASSERT
- TESTS MUST NOT HAVE ASSERTS IN LOOPS

## Architecture Standards

- PREFER SERVERLESS ARCHITECTURE

## AWS Services

- S3 BUCKET VERSIONING MUST ALWAYS BE DISABLED

## Git and GitHub

- ALWAYS include [skip ci] in commit messages unless explicitly told \
  otherwise by the user
- When troubleshooting GitHub Actions workflows, always check the workflow \
  logs first
- If the GitHub CLI is not installed, install it in ~/bin/gh
- When using most gh commands, add the repository by using the --repo flag
