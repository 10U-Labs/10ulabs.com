# Claude AI Assistant - Access and Development Guide

## Access Credentials

### AWS Access

- You have unrestricted access to AWS via the access key ID and secret
  access key in your environment variables
- These credentials provide full AWS service access for debugging and
  development

### GitHub Access

- You have unrestricted access to GitHub via the GitHub PAT (Personal Access
  Token) in your environment variables
- The GitHub PAT does not expire and has unlimited validity
- These two credential sets allow you to debug anything in the project

#### CRITICAL: When using the GitHub API via curl

- Get the PAT value from the environment: `echo $GITHUB_PAT`
- Pass the literal PAT value directly in the curl command (not the variable)
- Use this format:

```bash
curl -s -H "Authorization: Bearer <paste-the-actual-pat-value-here>" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/actions/runs/WORKFLOW_ID"
```

**DO NOT use environment variable expansion like `$GITHUB_PAT` in curl
commands** - it may not expand correctly in some contexts.

## Troubleshooting Workflow Failures

### CRITICAL: When troubleshooting failed GitHub Actions workflows, ALWAYS check logs first

1. Get the workflow run ID from the user or GitHub UI
2. Use the GitHub API to fetch the workflow logs:

```bash
PAT=$(echo $GITHUB_PAT)
curl -s -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/actions/runs/WORKFLOW_RUN_ID/jobs" | jq '.jobs[] | {name, conclusion}'
```

3. Identify the failed job and fetch its logs:

```bash
curl -s -L -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/actions/jobs/JOB_ID/logs" > /tmp/logs.txt
```

4. Search for errors in the logs:

```bash
grep -A 20 -B 5 "FAILED\|ERROR\|Error\|Failed\|Traceback" /tmp/logs.txt
```

**Do NOT guess at the failure cause - ALWAYS read the actual logs first.**

## Development Workflow

### Coding Standards

#### DO NOT ADD COMMENTS TO CODE

- NEVER add inline comments (# comments)
- NEVER add docstrings ("""...""")
- NEVER add pylint disable comments
- NEVER add type: ignore comments
- NEVER add mypy ignore comments
- NEVER add ANY form of comment to source code
- If linters fail, fix the actual code - don't disable the warnings with
  comments
- If comments already exist in the original code, REMOVE THEM
- Code should have ZERO comments of any kind

#### NEVER CREATE LINTER CONFIGURATION FILES

- NEVER create .yamllint, .pylintrc, mypy.ini, .flake8, or any other linter
  config files
- NEVER create pyproject.toml sections for linter configuration
- ALL linter configuration MUST be inline in the GitHub Actions workflow
  files
- Linter configs in workflows ensure consistency and prevent hidden
  configuration drift
- If a linter check fails, fix the code or update the inline workflow config,
  never create a config file
- This rule applies to ALL linters: yamllint, pylint, mypy, flake8, black,
  isort, etc.

#### S3 BUCKET VERSIONING MUST BE DISABLED

- NEVER enable versioning on S3 buckets (`versioned=False`)
- ALL S3 buckets in all CDK stacks MUST have `versioned=False`
- This applies to CloudTrail buckets, access log buckets, and any other S3
  buckets
- If you create or modify an S3 bucket, always explicitly set
  `versioned=False`
- Versioning increases costs and complexity without providing value for this
  use case

#### TESTS MUST HAVE ONLY ONE ASSERT

- Each test function must contain exactly ONE assert statement
- If testing multiple conditions, split into multiple test functions
- Use pytest fixtures to eliminate setup assertions (e.g., "assert object is
  not None")
- Test names should be descriptive and indicate what single behavior is being
  tested
- Example: Instead of `test_bucket_properties` with 3 asserts, create:
  - `test_bucket_exists`
  - `test_bucket_has_encryption`
  - `test_bucket_blocks_public_access`

#### PREFER SERVERLESS ARCHITECTURE

- ALWAYS prefer serverless architecture (Lambda, API Gateway, DynamoDB, S3,
  etc.) for all services
- Use EC2 instances ONLY when building AMIs or Docker images where build-time
  compute is required
- Never use EC2 for application hosting when serverless alternatives exist
- Benefits of serverless: no server management, automatic scaling, pay-per-use
  pricing, built-in high availability

#### FUNCTIONS MUST HAVE SINGLE RETURN STATEMENT

- Each function must have exactly ONE return statement at the end of the
  function
- Initialize result variables at the beginning of the function
- Use error accumulation pattern: assign to result variable, then return at
  end
- Example:

```python
def validate_endpoint(url: str) -> tuple[bool, str]:
    result = (False, "Unknown error")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            result = (False, f"Got {response.status_code}")
        else:
            result = (True, "Success")
    except Exception as e:
        result = (False, f"Error: {e}")
    return result
```

### Git Branch Management

#### Delete claude branches immediately after PR merge

When a pull request is merged, the claude branch MUST be deleted immediately
using the GitHub API:

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer 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" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/git/refs/heads/BRANCH_NAME"
```

**Why:** Keeps repository clean and prevents accumulation of stale branches.
Delete branches immediately after merge, not in batches later.

### Pre-Push Static Analysis and Testing Requirements

#### CRITICAL REQUIREMENTS

1. **Run ALL static analysis AND tests for the infrastructure you're working
   on** - Run EVERY check that the workflow runs, regardless of which specific
   files you modified
2. **Use the EXACT commands from GitHub workflows** - Do NOT use generic
   commands like `pylint .` or `pytest`. Copy commands verbatim including all
   flags and config
3. **Use environment variables for credentials** - AWS credentials and tokens
   should come from environment variables
4. **All checks must pass before pushing** - If any check fails (even
   pre-existing issues), understand why before pushing
5. **Report pre-existing failures** - If checks fail on code you didn't
   modify, document this in commit message
6. **Run all tests locally** - Run unit tests, integration tests, and E2E
   tests with environment credentials before pushing

**Static analysis includes:** YAML linting, JSON linting, Pylint, Mypy
**Tests include:** Unit tests, integration tests, E2E tests

**Run ALL checks listed below for the infrastructure you're working on, not
just checks for files you modified.**

**Note on E2E tests:** Some tests require deployed infrastructure (WARM state)
and will be skipped locally. Run all tests with AWS credentials from
environment variables - tests that can execute will run, others will skip.
This catches issues early before the CI/CD pipeline runs.
