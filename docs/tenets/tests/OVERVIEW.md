# Test Architecture Overview

This document is an inventory of this test suite: the levels the tests hang off, and the shared code that already exists so that none of it is written a second time. It describes what is here rather than saying where a new thing goes; that convention is in `CLAUDE.md` and the note it links.

## Table of Contents

- [Test Hierarchy](#test-hierarchy)
- [Directory Scope](#directory-scope)
- [Reusable Utilities in lib/python/](#reusable-utilities-in-libpython)
  - [test_fixtures/](#test_fixtures)
  - [terraform_config/](#terraform_config)
  - [terraform_drift/](#terraform_drift)
  - [naming_conventions/](#naming_conventions)
  - [boto_mocks/](#boto_mocks)
  - [event_factories/](#event_factories)
  - [lambda_response/](#lambda_response)
  - [module_utils/](#module_utils)
  - [test_utils/](#test_utils)
  - [urllib_mocks/](#urllib_mocks)
  - [repo_utils/](#repo_utils)
  - [lambda_http/](#lambda_http)

## Test Hierarchy

Tests follow a cascading conftest.py pattern. Each level inherits from parents and adds specifics.

```text
test/
├── conftest.py                              # Level 0: lib/python on sys.path, unit and AWS fixture plugins
├── api/
│   ├── conftest.py                          # Level 1: Terraform outputs, AWS clients, deployment probes
│   ├── endpoints/
│   │   ├── conftest.py                      # Level 2: fixtures every endpoint's tests use
│   │   └── sessions/
│   │       ├── conftest.py                  # Level 3: paths and config for the one endpoint
│   │       ├── pre_deployment/
│   │       │   ├── unit/conftest.py         # Level 4: Lambda loaders, patched environments
│   │       │   └── integration/conftest.py  # Level 4: layer markers, Terraform directories
│   │       └── post_deployment/
│   │           ├── integration/conftest.py  # Level 4: names of the deployed resources
│   │           └── e2e/conftest.py          # Level 4: endpoint URL and API key
│   ├── common/                              # the shared routing code, same shape
│   └── operational/                         # health and diagnostics, same shape
├── www/                                     # common/ and paths/<path>/, same tier split
├── bootstrap/                               # pre_deployment/ and post_deployment/ only
├── lib/                                     # mirrors lib/python/ and lib/terraform/, no tier split
└── scripts/
```

`sessions` is drawn here because it is the plainest of the endpoints. Some of the others add one more level, a conftest.py at the deployment-phase directory itself, for fixtures both tiers of that phase want; `test/api/endpoints/contact_submissions/pre_deployment/conftest.py` is one.

### What Each Level Holds

| Scope | Location | Examples |
| ------- | ---------- | ---------- |
| All tests | `test/conftest.py` | Path setup (already done) |
| All API tests | `test/api/conftest.py` | Terraform outputs, AWS clients, deployment probes |
| All endpoint tests | `test/api/endpoints/conftest.py` | The resource prefix, the handler-module loader, a mock Lambda context |
| One endpoint, both phases | `test/api/endpoints/<endpoint>/conftest.py` | That endpoint's source paths and its parsed config |
| Pre-deployment unit | `test/.../pre_deployment/unit/conftest.py` | Lambda mocks, event factories |
| Pre-deployment integration | `test/.../pre_deployment/integration/conftest.py` | Layer markers, bootstrap fixtures |
| Post-deployment integration | `test/.../post_deployment/integration/conftest.py` | Layer markers, AWS service clients |
| Post-deployment E2E | `test/.../post_deployment/e2e/conftest.py` | The deployed URL and the API key to call it with |

## Directory Scope

Three directories hold code the tests share, and they differ in how far that code reaches.

| Directory | Scope | Example Contents |
| ----------- | ------- | ------------------ |
| `lib/python/` | Entire codebase | `boto_mocks/`, `terraform_config/`, `test_fixtures/aws.py` |
| `test/` root | All tests | `conftest.py` (path setup), codebase-wide test utilities |
| `test/<module>/` | Module-specific | `test/www/conftest.py`, inline constants beside the tests that read them |

## Reusable Utilities in lib/python/

A package here is either loaded as a pytest plugin or imported directly, and which one is said below.

### test_fixtures/

The package a conftest.py loads as a pytest plugin. `test_fixtures.aws` holds the AWS fixtures and `test_fixtures.unit` the Lambda unit-testing ones; `test/conftest.py` loads both for the whole tree, so a suite that wants only these two loads nothing of its own.

```python
# In conftest.py
pytest_plugins = ['test_fixtures.aws']

# Provides these fixtures, among others:
# - shared_config: Parsed shared Terraform module config
# - aws_region: AWS region from config
# - state_bucket_name: Terraform state bucket
# - sts_client, iam_client, s3_client, ssm_client, ecr_client
# - lambda_client, apigateway_client, dynamodb_client, ses_client, logs_client
# - caller_identity, current_role_name
```

The rest of the package is imported rather than loaded as a plugin:

| Module | What it holds |
| -------- | --------------- |
| `test_fixtures.terraform` | `terraform_init`, `terraform_output` |
| `test_fixtures.config` | Config fixtures parsed from a `terraform.tfvars` or a `locals.tf` |
| `test_fixtures.website` | `create_website_fixtures`, used by both www suites |
| `test_fixtures.http_endpoint` | Checks on what a live endpoint's error responses give away |
| `test_fixtures.lambda_lifecycle` | Test factories for the lifecycle rules a Lambda with environment variables needs |
| `test_fixtures.terraform_tests` | Test factories for remote-state contracts and naming conventions |
| `test_fixtures.integration` | The base classes of the seven-layer pre-deployment integration model |

### terraform_config/

Parse Terraform configuration as single source of truth:

```python
from terraform_config import (
    get_shared_config,        # Combined locals + outputs + handlers
    get_tfvars_values,        # Parse terraform.tfvars
    get_resource_prefix,      # Resource naming prefix
    extract_lambda_function_names,  # Lambda names from .tf files
    TEST_AWS_REGION,          # Standard region for test mocks
)
```

### terraform_drift/

Detect orphaned resources (resources in AWS but not in Terraform state):

```python
from terraform_drift import check_resource_exists, get_planned_creates
from terraform_drift.test_helpers import create_orphaned_resource_tests

# Generate test class for orphaned resource detection
TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=TERRAFORM_DIR,
    region="us-east-2",
)
```

### naming_conventions/

Validate AWS resource names follow PascalCase:

```python
from naming_conventions import validate_name
from naming_conventions.test_helpers import (
    create_lambda_function_tests,
    create_iam_role_tests,
    create_sqs_queue_tests,
)

# Generate parametrized naming tests
TestLambdaNaming = create_lambda_function_tests(lambda_names)
```

### boto_mocks/

Factory functions for boto3 mocks in unit tests:

```python
from boto_mocks import (
    create_client_error,      # Create ClientError for error testing
    create_boto_client_mock,  # Create flexible boto3.client mock
    create_mock_lambda_with_mappings,
    create_mock_sns_publish_error,
)
```

### event_factories/

Create test Lambda event payloads:

```python
from event_factories import (
    create_sqs_event,              # SQS trigger event
    create_dlq_message,            # DLQ message format
)
```

### lambda_response/

Assert Lambda response structure:

```python
from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)
```

### module_utils/

Reset module state between tests (for Lambda handlers with cached clients):

```python
from module_utils import reset_module_state

def test_something(handler_module):
    reset_module_state(handler_module, boto_client=None, cache={})
```

### test_utils/

A loader that reaches an endpoint's handler module from the endpoint's own conftest:

```python
from test_utils import create_endpoint_handler_loader
```

### urllib_mocks/

Mock responses for handlers that call out with `urllib`:

```python
from urllib_mocks import create_mock_urllib_response
```

### repo_utils/

Find the repository root without hard-coding how deep a test file sits:

```python
from repo_utils import REPO_ROOT, extract_brace_block

TERRAFORM_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
```

The package below is imported by the Lambda handlers themselves rather than by tests, and is here because a test that asserts on a response shape should assert on the same helpers the handler builds it with.

### lambda_http/

Build and parse the HTTP shape a handler returns:

```python
from lambda_http import json_response, success_response, error_response, parse_body
```
