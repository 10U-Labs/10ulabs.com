# Development Guidelines

## Architecture Standards

- Prefer serverless architecture.

## Code Quality Standards

- If linters fail, fix the actual code.

## Credentials and Environment

- AWS credentials in `~/.aws/credentials` with unlimited privileges.
- GitHub CLI (`gh`) is already configured and authenticated locally with unlimited privileges.
- `GITHUB_PAT` environment variable contains a GitHub Personal Access Token with unlimited privileges.

## Git and GitHub

- Follow GitOps principles: all infrastructure and deployment changes must go through git commits and CI/CD workflows.

## Testing Standards

- Ensure full test coverage.
- Follow the testing pyramid: unit tests > integration tests > e2e tests.
- Most problems must be caught by unit tests.
- Use unit tests for everything except functionality that explicitly requires integration or e2e flows.
- Unit tests must be atomic and follow the single-responsibility principle.
