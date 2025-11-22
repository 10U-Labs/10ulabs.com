# Development Guidelines

## Architecture Standards

- Prefer serverless architecture.

## AWS Services

- S3 bucket versioning must always be disabled.

## Code Quality Standards

- Functions must have single return statement.
- If comments already exist in the original code, remove them.
- If linters fail, fix the actual code.
- Never add any form of comment to source code.
- Never add docstrings (`"""..."""`).
- Never add inline comments (`#` comments).
- Never create linter configuration files.
- Never disable lint checks.

## Credentials and Environment

- AWS credentials in ~/.aws/credentials with unlimited privileges.
- Do not use environment variable expansion like `$GITHUB_PAT` in `curl` commands, instead obtain the value first by running `echo $GITHUB_PAT` and passing the value literally.
- `GITHUB_PAT` has unlimited privileges in GitHub.
- GitHub Personal Access Token (PAT) in your environment variables as `GITHUB_PAT`.

## Git and GitHub

- Follow GitOps principles: all infrastructure and deployment changes must go through git commits and CI/CD workflows.
- Never deploy infrastructure locally (no local `cdk deploy`, `terraform apply`, etc.). Always commit changes and let workflows handle deployments.
- When troubleshooting GitHub Actions workflows, always check the workflow logs first.

## Testing Standards

- Tests must have only one assert.
- Tests must not use iteration (no loops, comprehensions, `all()`, `any()`, `in`, `.get()`, or other iterative operations).
