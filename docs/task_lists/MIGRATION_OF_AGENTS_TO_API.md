# Migration of Agents to API

## Overview

This plan covers 5 major changes:
1. Add exponential backoff to troubleshooter agent
2. Update README.md workflow dependency documentation
3. Update etc/workflow-dependencies.yml to reorder dependencies
4. Move src/agents → src/api/agents
5. Move test/agents → test/api/agents

---

## 1. Exponential Backoff Implementation

**File:** `src/api/agents/troubleshooter_of_workflows/webhook_lambda/handler.py`

- [x] Add `import random` and `import time` if not present
- [x] Add initial random delay (0-30 seconds) before processing each failure
- [x] Add exponential backoff loop: 2^4 (16s), 2^5 (32s), 2^6 (64s), 2^7 (128s), 2^8 (256s), 2^9 (512s)
- [x] Add warning logs for retries
- [x] Add error log when all retries exhausted

---

## 2. Update README.md Dependency Graph

**File:** `README.md`

- [x] Update ASCII diagram to show new hierarchy:
  - `www_shared` depends on `bootstrap` (not agents)
  - `agents_shared` depends on `endpoint_v1_runners`
  - All other agents depend on `agents_troubleshooter_of_workflows`

---

## 3. Update etc/workflow-dependencies.yml

**File:** `etc/workflow-dependencies.yml`

### Dependency Changes:
- [x] Change `www_shared.depends_on` from `agents_troubleshooter_of_workflows` to `bootstrap`
- [x] Change `agents_shared.depends_on` from `bootstrap` to `endpoint_v1_runners`

### Path Updates (all agent entries):
- [x] `agents_shared` paths: `src/agents/shared/**` → `src/api/agents/shared/**`
- [x] `agents_shared` paths: `test/agents/shared/**` → `test/api/agents/shared/**`
- [x] `agents_troubleshooter_of_workflows` paths updated
- [x] `agents_agent_creator` paths updated
- [x] `agents_agent_deleter` paths updated
- [x] `agents_agent_evaluator` paths updated
- [x] `agents_agent_modifier` paths updated
- [x] `agents_code_reviewer_for_pre_deployment_integration_tests` paths updated
- [x] `agents_creator_of_e2e_tests` paths updated
- [x] `agents_creator_of_post_deployment_integration_tests` paths updated
- [x] `agents_creator_of_pre_deployment_integration_tests` paths updated
- [x] `agents_creator_of_unit_tests` paths updated
- [x] `agents_deleter_of_e2e_tests` paths updated
- [x] `agents_deleter_of_post_deployment_integration_tests` paths updated
- [x] `agents_deleter_of_pre_deployment_integration_tests` paths updated
- [x] `agents_deleter_of_unit_tests` paths updated
- [x] `agents_modifier_of_e2e_tests` paths updated
- [x] `agents_modifier_of_post_deployment_integration_tests` paths updated
- [x] `agents_modifier_of_pre_deployment_integration_tests` paths updated
- [x] `agents_modifier_of_unit_tests` paths updated
- [x] `agents_workflow_creator` paths updated
- [x] `agents_workflow_deleter` paths updated
- [x] `agents_workflow_evaluator` paths updated
- [x] `agents_workflow_modifier` paths updated

---

## 4. Move src/agents → src/api/agents

### Directory Moves:
- [x] Move `src/agents/shared/` → `src/api/agents/shared/`
- [x] Move `src/agents/troubleshooter_of_workflows/` → `src/api/agents/troubleshooter_of_workflows/`
- [x] Move `src/agents/agent_creator/` → `src/api/agents/agent_creator/`
- [x] Move `src/agents/code_reviewer_for_pre_deployment_integration_tests/` → `src/api/agents/code_reviewer_for_pre_deployment_integration_tests/`
- [x] Move any other agent directories

### Workflow File Updates (.github/workflows/agents_*.yml):
- [x] `agents_shared.yml` - update `cd src/agents/shared` → `cd src/api/agents/shared`
- [x] `agents_troubleshooter_of_workflows.yml` - update paths
- [x] `agents_agent_creator.yml` - update paths
- [x] `agents_agent_deleter.yml` - update paths
- [x] `agents_agent_evaluator.yml` - update paths
- [x] `agents_agent_modifier.yml` - update paths
- [x] `agents_code_reviewer_for_pre_deployment_integration_tests.yml` - update paths
- [x] `agents_creator_of_e2e_tests.yml` - update paths
- [x] `agents_creator_of_post_deployment_integration_tests.yml` - update paths
- [x] `agents_creator_of_pre_deployment_integration_tests.yml` - update paths
- [x] `agents_creator_of_unit_tests.yml` - update paths
- [x] `agents_deleter_of_e2e_tests.yml` - update paths
- [x] `agents_deleter_of_post_deployment_integration_tests.yml` - update paths
- [x] `agents_deleter_of_pre_deployment_integration_tests.yml` - update paths
- [x] `agents_deleter_of_unit_tests.yml` - update paths
- [x] `agents_modifier_of_e2e_tests.yml` - update paths
- [x] `agents_modifier_of_post_deployment_integration_tests.yml` - update paths
- [x] `agents_modifier_of_pre_deployment_integration_tests.yml` - update paths
- [x] `agents_modifier_of_unit_tests.yml` - update paths
- [x] `agents_workflow_creator.yml` - update paths
- [x] `agents_workflow_deleter.yml` - update paths
- [x] `agents_workflow_evaluator.yml` - update paths
- [x] `agents_workflow_modifier.yml` - update paths

**Note:** Keep S3 Terraform state keys unchanged (`agents/...`) to avoid state migration.

---

## 5. Move test/agents → test/api/agents

### Directory Moves:
- [x] Move `test/agents/shared/` → `test/api/agents/shared/`
- [x] Move `test/agents/troubleshooter_of_workflows/` → `test/api/agents/troubleshooter_of_workflows/`
- [x] Move `test/agents/agent_creator/` → `test/api/agents/agent_creator/`
- [x] Move `test/agents/code_reviewer_for_pre_deployment_integration_tests/` → `test/api/agents/code_reviewer_for_pre_deployment_integration_tests/`
- [x] Move any other agent test directories

### conftest.py Updates:
- [x] Update `test/api/agents/shared/pre_deployment/conftest.py` - fix `AGENTS_SHARED_DIR` path
- [x] Update any `Path(__file__).parents[N]` references for new depth

### Test File Updates:
- [x] Update `test/api/agents/troubleshooter_of_workflows/pre_deployment/unit/test_handler.py` - fix source path reference
- [x] Update `test/api/agents/agent_creator/pre_deployment/unit/test_handler.py` - fix source path reference

---

## Execution Order

1. [x] **Exponential backoff** - standalone change, do first
2. [x] **Directory moves** - `src/agents` → `src/api/agents`
3. [x] **Directory moves** - `test/agents` → `test/api/agents`
4. [x] **Update workflow files** - all `.github/workflows/agents_*.yml`
5. [x] **Update etc/workflow-dependencies.yml** - paths AND dependency order
6. [x] **Update README.md** - new diagram

---

## New Dependency Hierarchy

```
bootstrap
    │
    ├── www_shared
    │       │
    │       └── api_backend
    │               │
    │               └── endpoint_health
    │                       │
    │                       ├── api_shared_runners ─────────────────────────────────┐
    │                       │       │                                                │
    │                       │       └── endpoint_v1_image_for_ec2_runners_post       │
    │                       │               │                                        │
    │                       │               └── endpoint_v1_image_for_ec2_runners    │
    │                       │                       │                                │
    │                       │                       └── endpoint_v1_ec2_runner ──────┤
    │                       │                                                        │
    │                       └── api_shared_ecs_runner ───────────────────────────────┤
    │                                                                                │
    │                                               endpoint_v1_image_for_ecs_runners
    │                                                            │
    │                                               endpoint_v1_ecs_runner ──────────┤
    │                                                                                │
    │                                                                     endpoint_v1_runners
    │                                                                                │
    │                                 ┌───────────────────────────┬──────────────────┼──────────────────────┐
    │                                 │                           │                  │                      │
    │                         endpoint_v1_echo           endpoint_v1_contact         │         endpoint_v1_rack_designer
    │                                                             │                  │                      │
    │                                                        www_index               │         endpoint_v1_simulation_soc
    │                                                                                │
    └────────────────────────────────────────────────────────────────────────────────┤
                                                                                     │
                                                                              agents_shared
                                                                                     │
                                                              agents_troubleshooter_of_workflows
                                                                                     │
                                                              ┌──────────────────────┼──────────────────────┐
                                                              │                      │                      │
                                                      agents_agent_*        agents_workflow_*       agents_*_of_*_tests
```
