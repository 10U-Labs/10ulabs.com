# Claude AI Assistant - Access and Development Guide

## Access Credentials

### AWS Access
- You have unrestricted access to AWS via the access key ID and secret access key in your environment variables
- These credentials provide full AWS service access for debugging and development

### GitHub Access
- You have unrestricted access to GitHub via the GitHub PAT (Personal Access Token) in your environment variables
- The GitHub PAT does not expire and has unlimited validity
- These two credential sets allow you to debug anything in the project

**CRITICAL: When using the GitHub API via curl:**
- Get the PAT value from the environment: `echo $GITHUB_PAT`
- Pass the literal PAT value directly in the curl command (not the variable)
- Use this format:
```bash
curl -s -H "Authorization: Bearer <paste-the-actual-pat-value-here>" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/actions/runs/WORKFLOW_ID"
```

**DO NOT use environment variable expansion like `$GITHUB_PAT` in curl commands** - it may not expand correctly in some contexts.

## Troubleshooting Workflow Failures

**CRITICAL: When troubleshooting failed GitHub Actions workflows, ALWAYS check logs first:**

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

**CRITICAL: DO NOT ADD COMMENTS TO CODE**
- NEVER add inline comments (# comments)
- NEVER add docstrings ("""...""")
- NEVER add pylint disable comments
- NEVER add type: ignore comments
- NEVER add mypy ignore comments
- NEVER add ANY form of comment to source code
- If linters fail, fix the actual code - don't disable the warnings with comments
- If comments already exist in the original code, REMOVE THEM
- Code should have ZERO comments of any kind

**CRITICAL: S3 BUCKET VERSIONING MUST BE DISABLED**
- NEVER enable versioning on S3 buckets (`versioned=False`)
- ALL S3 buckets in all CDK stacks MUST have `versioned=False`
- This applies to CloudTrail buckets, access log buckets, and any other S3 buckets
- If you create or modify an S3 bucket, always explicitly set `versioned=False`
- Versioning increases costs and complexity without providing value for this use case

**CRITICAL: TESTS MUST HAVE ONLY ONE ASSERT**
- Each test function must contain exactly ONE assert statement
- If testing multiple conditions, split into multiple test functions
- Use pytest fixtures to eliminate setup assertions (e.g., "assert object is not None")
- Test names should be descriptive and indicate what single behavior is being tested
- Example: Instead of `test_bucket_properties` with 3 asserts, create:
  - `test_bucket_exists`
  - `test_bucket_has_encryption`
  - `test_bucket_blocks_public_access`

**CRITICAL: PREFER SERVERLESS ARCHITECTURE**
- ALWAYS prefer serverless architecture (Lambda, API Gateway, DynamoDB, S3, etc.) for all services
- Use EC2 instances ONLY when building AMIs or Docker images where build-time compute is required
- Never use EC2 for application hosting when serverless alternatives exist
- Benefits of serverless: no server management, automatic scaling, pay-per-use pricing, built-in high availability

### Commit Message Flags

Use these flags in commit messages to control workflow behavior:

**`[post-deployment]`** - Skip all pre-deployment steps, run only post-deployment tests
- Skips: Static analysis, unit tests, integration tests, building, deployment
- Runs: Post-deployment integration tests, E2E tests
- Use when: Testing changes to post-deployment test files only

**`[skip-deploy]`** or **`[skip deploy]`** - Run all checks but skip actual deployment
- Runs: Static analysis, unit tests, integration tests, building
- Skips: Deployment step only
- Use when: Testing changes that don't need deployment

**Examples:**
- `[post-deployment] Fix E2E DNS resolution tests` - Only runs post-deployment tests
- `[skip-deploy] Update CDK stack configuration` - Runs all checks but no deployment

### Git Branch Management

**CRITICAL: Delete claude branches immediately after PR merge**

When a pull request is merged, the claude branch MUST be deleted immediately using the GitHub API:

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer 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" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/10U-Labs-LLC/10ulabs.com/git/refs/heads/BRANCH_NAME"
```

**Why:** Keeps repository clean and prevents accumulation of stale branches. Delete branches immediately after merge, not in batches later.

### Pre-Push Static Analysis and Testing Requirements

**CRITICAL REQUIREMENTS:**
1. **Run ALL static analysis AND tests for the infrastructure you're working on** - Run EVERY check that the workflow runs, regardless of which specific files you modified
2. **Use the EXACT commands from GitHub workflows** - Do NOT use generic commands like `pylint .` or `pytest`. Copy commands verbatim including all flags and config
3. **Use environment variables for credentials** - AWS credentials and tokens should come from environment variables
4. **All checks must pass before pushing** - If any check fails (even pre-existing issues), understand why before pushing
5. **Report pre-existing failures** - If checks fail on code you didn't modify, document this in commit message
6. **Run post-deployment tests** - Run as many post-deployment tests as possible with environment credentials before pushing

**Static analysis includes:** YAML linting, JSON linting, Markdown linting, Pylint, Mypy
**Tests include:** Unit tests, pre-deployment integration tests, post-deployment integration tests, E2E tests

**Run ALL checks listed below for the infrastructure you're working on, not just checks for files you modified.**

**Post-deployment tests:** Some tests require deployed infrastructure (WARM state) and will be skipped locally. Run all post-deployment tests that can execute with just AWS credentials from environment variables. This catches issues early before the CI/CD pipeline runs.

---

## AWS-GitHub Auth Infrastructure Tests

Run these tests if you modified `src/auth_between_aws_and_github/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/auth_between_aws_and_github.yml
```

#### 2. JSON Configuration Linting
```bash
jsonlint -q src/auth_between_aws_and_github/config.json
```

#### 3. Markdown Documentation Linting (if README exists)
```bash
markdownlint-cli2 src/auth_between_aws_and_github/README.md
```

**NOTE:** This will only run if README.md exists. All default markdownlint rules are enforced.

#### 4. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pylint src/auth_between_aws_and_github/stack.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 5. Python Static Type Checking (Mypy)
```bash
mypy src/auth_between_aws_and_github
```

#### 6. Unit Tests
```bash
pytest test/auth_between_aws_and_github/test_unit.py -v
```

#### 7. Integration Tests

**IMPORTANT:** Integration tests require AWS credentials in environment variables. Check credentials first:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
echo "GITHUB_PAT: ${GITHUB_PAT:0:10}..."
```

Run integration tests (uses environment variables automatically):
```bash
pytest test/auth_between_aws_and_github/test_integration.py -v
```

**Required environment variables:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SESSION_TOKEN` - (optional) AWS session token if using temporary credentials
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `GITHUB_PAT` - GitHub Personal Access Token

#### 8. E2E Tests

**IMPORTANT:** Run E2E tests with environment credentials.

Check credentials are available:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
echo "GITHUB_PAT: ${GITHUB_PAT:0:10}..."
```

Run E2E tests (uses environment variables automatically):
```bash
pytest test/auth_between_aws_and_github/test_e2e.py -v
```

**Note:** Tests requiring deployed infrastructure (WARM state) will be skipped. Tests that can run with just AWS credentials will execute.

---

## CloudTrail and Domain Name Tests

Run these tests if you modified `src/cloudtrail_and_domain_name/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/cloudtrail_and_domain_name.yml
```

#### 2. JSON Configuration Linting
```bash
jsonlint -q src/cloudtrail_and_domain_name/config.json
```

#### 3. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pylint src/cloudtrail_and_domain_name/stack.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines,too-many-locals \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 4. Python Static Type Checking (Mypy)
**First install dependencies:**
```bash
pip install -r src/cloudtrail_and_domain_name/requirements.txt
```

**Then run mypy:**
```bash
mypy src/cloudtrail_and_domain_name
```

#### 5. Unit Tests
**Requires CDK dependencies installed (see step 4):**
```bash
pytest test/cloudtrail_and_domain_name/test_unit.py -v
```

#### 6. Integration Tests

**IMPORTANT:** Requires CDK dependencies (see step 4) and AWS credentials in environment variables.

Check credentials first:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run integration tests (uses environment variables automatically):
```bash
pytest test/cloudtrail_and_domain_name/test_integration.py -v
```

**Required environment variables:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SESSION_TOKEN` - (optional) AWS session token if using temporary credentials
- `AWS_REGION` - AWS region (e.g., us-east-1)

#### 7. E2E Tests

**IMPORTANT:** Run E2E tests with environment credentials.

Check credentials are available:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run E2E tests (uses environment variables automatically):
```bash
pytest test/cloudtrail_and_domain_name/test_e2e.py -v
```

**Note:** Tests requiring deployed infrastructure (WARM state) will be skipped. Tests that can run with just AWS credentials will execute.

---

## API Infrastructure Tests

Run these tests if you modified `src/api/self/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/api.yml
```

#### 2. JSON Configuration Linting
```bash
jsonlint -q src/api/self/config.json
jsonlint -q src/api/self/cdk.json
```

#### 3. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pylint src/api/self/stack.py src/api/self/lambda/handler.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines,too-many-locals \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 4. Python Static Type Checking (Mypy)
**First install dependencies:**
```bash
pip install -r src/api/self/requirements.txt
```

**Then run mypy:**
```bash
mypy src/api/self
```

#### 5. Unit Tests
**Requires CDK dependencies installed (see step 4):**
```bash
pytest test/api/test_unit.py -v
```

#### 6. Integration Tests

**IMPORTANT:** Requires CDK dependencies (see step 4) and AWS credentials in environment variables.

Check credentials first:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run integration tests (uses environment variables automatically):
```bash
pytest test/api/test_integration.py -v
```

**Required environment variables:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SESSION_TOKEN` - (optional) AWS session token if using temporary credentials
- `AWS_REGION` - AWS region (e.g., us-east-1)

#### 7. E2E Tests

**IMPORTANT:** Run E2E tests with environment credentials.

Check credentials are available:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run E2E tests (uses environment variables automatically):
```bash
pytest test/api/test_e2e.py -v
```

**Note:** Tests requiring deployed infrastructure (WARM state) will be skipped. Tests that can run with just AWS credentials will execute.

---

## Gmail Email Provider Tests

Run these tests if you modified `src/gmail_email_provider/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/gmail_email_provider.yml
```

#### 2. JSON Configuration Linting
```bash
jsonlint -q src/gmail_email_provider/config.json
jsonlint -q src/gmail_email_provider/cdk.json
```

#### 3. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pylint src/gmail_email_provider/stack.py src/gmail_email_provider/app.py scripts/readme.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 4. Python Static Type Checking (Mypy)
**First install dependencies:**
```bash
pip install -r src/gmail_email_provider/requirements.txt
```

**Then run mypy:**
```bash
mypy src/gmail_email_provider
```

#### 5. Unit Tests
**Requires CDK dependencies installed (see step 4):**
```bash
pytest test/gmail_email_provider/test_unit.py -v
```

#### 6. Integration Tests

**IMPORTANT:** Requires CDK dependencies (see step 4) and AWS credentials in environment variables.

Check credentials first:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run integration tests (uses environment variables automatically):
```bash
pytest test/gmail_email_provider/test_integration.py -v
```

**Required environment variables:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SESSION_TOKEN` - (optional) AWS session token if using temporary credentials
- `AWS_REGION` - AWS region (e.g., us-east-1)

#### 7. E2E Tests

**IMPORTANT:** Run E2E tests with environment credentials.

Check credentials are available:
```bash
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"
```

Run E2E tests (uses environment variables automatically):
```bash
pytest test/gmail_email_provider/test_e2e.py -v
```

**Note:** Tests requiring deployed infrastructure (WARM state) will be skipped. Tests that can run with just AWS credentials will execute.

---

### Pre-Push Checklist

**CRITICAL: Before creating PR, verify ALL of the following (for the infrastructure you modified):**

**Static Analysis:**
- [ ] All relevant YAML files pass `yamllint`
- [ ] JSON config files pass `jsonlint` validation
- [ ] Markdown README passes `markdownlint-cli2` (if applicable)
- [ ] Pylint passes with `--fail-under=10.0` using exact workflow flags (if applicable)
- [ ] Mypy passes with no errors

**Tests:**
- [ ] All relevant pre-deployment unit tests pass
- [ ] All relevant pre-deployment integration tests pass (with environment variable credentials)
- [ ] All relevant post-deployment integration tests pass (with environment variable credentials)
- [ ] All relevant post-deployment E2E tests pass (with environment variable credentials)

**General:**
- [ ] Code changes are committed with clear, descriptive messages
- [ ] Used EXACT commands from GitHub workflows (not generic commands)
- [ ] Documented any pre-existing test failures that aren't from your changes

**All static analysis checks and tests must pass before creating PR to ensure code quality and prevent breaking changes.**
