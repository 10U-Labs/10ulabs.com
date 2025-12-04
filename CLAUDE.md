# Development Guidelines

## Architecture Standards

- Prefer serverless architecture.

## AWS Services

- S3 bucket versioning must always be disabled.

## Code Quality Standards

- Functions must have single exit point.
- Functions must have a single return statement.
- If linters fail, fix the actual code.
- Never create linter configuration files.
- Never disable lint checks.
- Never use `break` nor `continue` statements.

## Credentials and Environment

- AWS credentials in `~/.aws/credentials` with unlimited privileges.
- GitHub CLI (`gh`) is already configured and authenticated locally with unlimited privileges.
- `GITHUB_PAT` environment variable contains a GitHub Personal Access Token with unlimited privileges.

## Git and GitHub

- Follow GitOps principles: all infrastructure and deployment changes must go through git commits and CI/CD workflows.
- Never deploy infrastructure locally (no local `cdk deploy`, `terraform apply`, etc.). Always commit changes and let workflows handle deployments.
- Never use `gh run watch` as it requires interactive input.
- Never use `sleep` when executing the Bash tool.

## Testing Standards

- Ensure full test coverage.
- Follow the testing pyramid: unit tests > integration tests > e2e tests.
- Most problems must be caught by unit tests.
- Use unit tests for everything except functionality that explicitly requires integration or e2e flows.
- Unit tests must be atomic and follow the single-responsibility principle.
- Tests must have only one assert.
- Asserts in tests must have a single variable in the format `{noun_phrase}_{verb}` or `{noun_phrase}_{verb}_{adjective|adverb}`. The noun phrase must be descriptive enough to make the assertion intuitive (e.g., `assert python_script_to_invalidate_cloudfront_exists`, not `assert file_exists`).
