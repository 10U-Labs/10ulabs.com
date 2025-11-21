# Development Guidelines

## Credentials and Environment

- AWS access key ID in your environment variables as `AWS_ACCESS_KEY_ID`.
- AWS secret key in your environment variables as `AWS_SECRET_ACCESS_KEY`.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` have unlimited privileges in AWS.
- GitHub Personal Access Token (PAT) in your environment variables as `GITHUB_PAT`.
- `GITHUB_PAT` has unlimited privileges in GitHub.
- Do not use environment variable expansion like `$GITHUB_PAT` in `curl` commands, instead obtain the value first by running `echo $GITHUB_PAT` and passing the value literally.

## Code Quality Standards

- Never add any form of comment to source code.
- If comments already exist in the original code, remove them.
- Never add inline comments (`#` comments).
- Never add docstrings (`"""..."""`).
- Never disable lint checks.
- If linters fail, fix the actual code.
- Never create linter configuration files.
- Functions must have single return statement.

## Testing Standards

- Tests must have only one assert.
- Tests must not have asserts in loops.

## Architecture Standards

- Prefer serverless architecture.

## AWS Services

- S3 bucket versioning must always be disabled.

## Git and GitHub

- Follow GitOps principles: all infrastructure and deployment changes must go through git commits and CI/CD workflows.
- Never deploy infrastructure locally (no local `cdk deploy`, `terraform apply`, etc.). Always commit changes and let workflows handle deployments.
- When troubleshooting GitHub Actions workflows, always check the workflow logs first.
- If the GitHub CLI is not installed, install it in `~/bin/gh`.
- When using most `gh` commands, add the repository by using the `--repo` flag.
