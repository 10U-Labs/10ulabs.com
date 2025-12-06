# Workflow Ordering System

This document describes the workflow ordering system that ensures GitHub Actions workflows deploy in the correct dependency order.

## Overview

When a commit affects multiple workflows, they must deploy in a specific order based on their dependencies. For example, the ECR workflow must complete before image-building workflows, and shared infrastructure must deploy before endpoints that depend on it.

## Configuration

The workflow dependency graph is defined in `.github/workflow-order.yml`:

```yaml
workflows:
  bootstrap:
    level: 0
    description: "Foundation - IAM, S3, Route53"
    depends_on: []

  ecr:
    level: 1
    description: "ECR repositories"
    depends_on:
      - bootstrap

  runners:
    level: 2
    description: "Runner infrastructure"
    depends_on:
      - ecr
```

### Fields

- **level**: Numeric deployment order (0 = first, higher = later)
- **description**: Human-readable description of the workflow's purpose
- **depends_on**: List of workflow names that must complete before this workflow

## Deployment Order

```
Level 0: bootstrap (foundation - IAM, S3, Route53)
    ↓
Level 1: ecr, www_shared (shared resources)
    ↓
Level 2: runners, api (runner infra, API Gateway)
    ↓
Level 3: image_for_ecs_runners, image_for_ec2_runners_* (runner images)
    ↓
Level 4: ecs_runner, ec2_runner (runner endpoints)
    ↓
Level 5: All other endpoints (health, echo, contact, etc.)
```

## How It Works

### 1. Workflow Detection

When a commit is pushed, the system identifies affected workflows by matching changed files against each workflow's `on.push.paths` configuration.

### 2. Dependency Resolution

The `lib/workflow_ordering.py` module provides:

- `parse_workflow_order(yaml_path)` - Parse the dependency graph from YAML
- `get_affected_workflows(changed_files)` - Determine which workflows are affected
- `get_deployment_order(affected)` - Topological sort for correct order
- `should_wait_for(workflow, completed)` - Check if dependencies are met

### 3. Orchestration

Each workflow includes a `workflow_call` trigger that allows the orchestrator to invoke it. Workflows check their dependencies before running using the check-dependencies workflow.

## Usage

### Adding a New Workflow

1. Add the workflow to `.github/workflow-order.yml`:

```yaml
workflows:
  my_new_workflow:
    level: 3
    description: "My new workflow"
    depends_on:
      - runners
      - ecr
```

2. Add `workflow_call` trigger to the workflow file:

```yaml
on:
  workflow_call:
  push:
    paths:
      - 'src/api/endpoints/my_endpoint/**'
```

### Running Locally

The pre-commit hook runs static analysis from affected workflows before allowing commits. Integration tests (which require AWS resources) are skipped locally and run only in CI.

## API Reference

### parse_workflow_order(yaml_path: str) -> Dict

Parse the workflow order YAML file and return a dictionary of workflow configurations.

**Raises**: `ValueError` if circular dependencies are detected.

### get_affected_workflows(changed_files: List[str]) -> List[str]

Given a list of changed files, return the list of workflow names that are affected.

### get_deployment_order(affected: List[str]) -> List[str]

Given a list of affected workflow names, return them in topologically sorted order based on their dependencies.

### should_wait_for(workflow: str, completed: Set[str]) -> bool

Check if a workflow should wait for its dependencies. Returns `True` if all dependencies are in the `completed` set.

## Testing

Unit tests for the workflow ordering system are in `test/lib/test_workflow_ordering.py`:

```bash
pytest test/lib/test_workflow_ordering.py -v
```

Tests cover:
- YAML parsing (valid and invalid)
- Circular dependency detection
- Affected workflow detection
- Topological sorting
- Diamond dependency patterns
- Dependency completion checking
