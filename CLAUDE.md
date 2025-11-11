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

### Branch and PR Strategy
- **Create PRs to main** - After pushing to your claude/ branch, create a pull request
- **Merge immediately** - Do NOT wait for CI checks to pass; merge the PR immediately after creation
- **Clean up remote branches** - Delete remote claude/ branches after merging (local branch is irrelevant)
- When creating PRs, use descriptive titles and comprehensive summaries

### PR Creation Workflow
After completing work, committing, and running all required pre-deployment tests:
1. Push commits to the claude/ branch
2. Create pull request to main with descriptive title and comprehensive summary
3. Immediately merge the PR and delete the remote branch
4. CI/CD will run post-deployment after merge

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

### Pre-Push Testing Requirements

**CRITICAL: Only run pre-deployment tests for the infrastructure you modified.** Don't run all tests if you only changed one stack.

Run the following pre-deployment checks locally before pushing. **CRITICAL: Use the EXACT commands that the GitHub workflows use, not generic commands.**

---

## AWS-GitHub Auth Infrastructure Tests

Run these tests if you modified `src/auth_between_aws_and_github/` or `test/auth_between_aws_and_github/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/auth_between_aws_and_github.yml
```

#### 2. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pylint src/auth_between_aws_and_github/auth_between_aws_and_github.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 3. Python Static Type Checking (Mypy)
```bash
mypy src/auth_between_aws_and_github/auth_between_aws_and_github.py
```

#### 4. Unit Tests
```bash
PYTHONPATH=src/bootstrap:$PYTHONPATH pytest test/auth_between_aws_and_github/pre_deployment/test_unit.py -v
```

#### 5. Integration Tests
```bash
pytest test/auth_between_aws_and_github/pre_deployment/test_integration.py -v
```

**NOTE:** Integration tests may require AWS credentials in environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `GH_RUNNER_PAT`

---

## CloudTrail and Domain Name Tests

Run these tests if you modified `src/cloudtrail_and_domain_name/` or `test/cloudtrail_and_domain_name/`:

#### 1. YAML Linting
```bash
yamllint .github/workflows/cloudtrail_and_domain_name.yml
```

#### 2. Python Code Linting (Pylint)
**Use the exact workflow command with all the same flags:**
```bash
pip install -q pylint
pylint src/cloudtrail_and_domain_name/stack.py src/cloudtrail_and_domain_name/lambda/handler.py \
  --disable=line-too-long,missing-class-docstring,missing-function-docstring,missing-module-docstring,too-many-lines \
  --fail-under=10.0
```

**IMPORTANT:** Do NOT run `pylint` without these flags. The workflow requires `--fail-under=10.0` with specific disables.

#### 3. Python Static Type Checking (Mypy)
**First install dependencies:**
```bash
pip install -q -r requirements-cdk.txt
```

**Then run mypy:**
```bash
mypy src/cloudtrail_and_domain_name
```

#### 4. Unit Tests
**Requires CDK dependencies installed (see step 3):**
```bash
python -m pytest test/cloudtrail_and_domain_name/pre_deployment/unit/test_unit.py -v
```

#### 5. Integration Tests
**Requires CDK dependencies installed (see step 3):**
```bash
python -m pytest test/cloudtrail_and_domain_name/pre_deployment/integration/test_integration.py -v
```

**NOTE:** Integration tests may require AWS credentials in environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

---

### Pre-Deployment Checklist

Before creating PR, verify (for the infrastructure you modified):
- [ ] All relevant YAML files pass `yamllint`
- [ ] Pylint passes with `--fail-under=10.0` using exact workflow flags (if applicable)
- [ ] Mypy passes with no errors
- [ ] All relevant pre-deployment unit tests pass
- [ ] All relevant pre-deployment integration tests pass (or are appropriately skipped)
- [ ] Code changes are committed with clear, descriptive messages

**All pre-deployment tests and checks must pass before creating PR to ensure code quality and prevent breaking changes.**
