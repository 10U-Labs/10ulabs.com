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
- Never use `sleep`.

## Credentials and Environment

- AWS credentials in `~/.aws/credentials` with unlimited privileges.
- GitHub CLI (`gh`) is already configured and authenticated locally with unlimited privileges.
- `GITHUB_PAT` environment variable contains a GitHub Personal Access Token with unlimited privileges.

## Git and GitHub

- Follow GitOps principles: all infrastructure and deployment changes must go through git commits and CI/CD workflows.
- Never deploy infrastructure locally (no local `cdk deploy`, `terraform apply`, etc.). Always commit changes and let workflows handle deployments.
- Never use `gh run watch` as it requires interactive input.

## Testing Standards

- Ensure full test coverage.
- Follow the testing pyramid: unit tests > integration tests > e2e tests.
- Align with the typical 5:2:1 ratio (unit:integration:e2e).
- Most problems must be caught by unit tests.
- Use unit tests for everything except functionality that explicitly requires integration or e2e flows.
- Unit tests must be atomic and follow the single-responsibility principle.
- Tests must have only one assert.
- Asserts in tests must have a single variable only (e.g., `assert such_thing_is_true` or `assert such_thing_is_false`).
