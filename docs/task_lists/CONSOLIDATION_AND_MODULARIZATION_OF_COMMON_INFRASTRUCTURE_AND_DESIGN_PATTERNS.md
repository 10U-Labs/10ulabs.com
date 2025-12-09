# Infrastructure Consolidation Plan

## Overview

Consolidate scattered infrastructure into bootstrap and create reusable modules to reduce duplication and ensure single source of truth for shared resources.

## Current State

| Resource | Current Locations | Issues |
|----------|-------------------|--------|
| ECR Repos (4) | `src/api/shared/ecr/`, `src/agents/{agent_creator,workflow_fixer}/ecr.tf`, `src/agents/test_auditor/bedrock.tf` | Duplicated config, separate lifecycle policies |
| VPC | `src/api/endpoints/runners/vpc.tf` | Should be shared infrastructure |
| Security Groups | `src/api/endpoints/runners/vpc.tf` | Coupled to VPC location |
| S3 Buckets | `src/api/backend/cloudfront_s3.tf`, `src/www/shared/cloudfront_s3.tf` | Duplicated patterns (versioning, encryption, logging, public access blocking) |

## Target State

```
src/bootstrap/
├── ecr.tf                    # All ECR repositories
├── vpc.tf                    # Shared VPC for compute resources
├── security_groups.tf        # Shared security groups
└── outputs.tf                # Expanded with new outputs

lib/terraform/modules/
└── s3-bucket/               # Reusable S3 bucket module
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

---

## Phase 1: ECR Consolidation

### 1.1 Create consolidated ECR in bootstrap
- [x] Create `src/bootstrap/ecr.tf` with runners repository
- [x] Add agents repository to `src/bootstrap/ecr.tf`
- [x] Configure lifecycle policies for runners (keep 1 latest + 1 stable)
- [x] Configure lifecycle policies for agents (keep last 5 per agent)

### 1.2 Update bootstrap outputs
- [x] Add `ecr_runners_repository_arn` output
- [x] Add `ecr_runners_repository_name` output
- [x] Add `ecr_runners_repository_url` output
- [x] Add `ecr_agents_repository_arn` output
- [x] Add `ecr_agents_repository_name` output
- [x] Add `ecr_agents_repository_url` output

### 1.3 Update consumers
- [x] `src/api/endpoints/runners/data.tf` - Reference bootstrap instead of ecr state
- [x] `src/api/endpoints/ecs_runner/data.tf` - Reference bootstrap instead of ecr state
- [x] `src/api/endpoints/ecs_runner/ecs.tf` - Use bootstrap ECR URL
- [x] `src/api/endpoints/ec2_runner/lambda.tf` - Use bootstrap ECR URL
- [x] `src/api/endpoints/image_for_ecs_runners/locals.tf` - Use bootstrap ECR URL
- [x] `src/agents/agent_creator/agentcore.tf` - Use bootstrap ECR URL with agent-creator tag
- [x] `src/agents/agent_creator/locals.tf` - Update image tag format
- [x] `src/agents/agent_creator/iam.tf` - No update needed (uses wildcards)
- [x] `src/agents/workflow_fixer/agentcore.tf` - Use bootstrap ECR URL with workflow-fixer tag
- [x] `src/agents/workflow_fixer/locals.tf` - Update image tag format
- [x] `src/agents/workflow_fixer/iam.tf` - Update ECR ARN reference
- [x] `src/agents/test_auditor/bedrock.tf` - Use bootstrap ECR URL with test_auditor tag
- [x] `src/agents/test_auditor/locals.tf` - Update image tag format
- [x] `src/agents/test_auditor/iam.tf` - Update ECR ARN reference

### 1.4 Remove old ECR definitions
- [x] Delete `src/api/shared/ecr/` directory
- [x] Delete `src/agents/agent_creator/ecr.tf`
- [x] Delete `src/agents/workflow_fixer/ecr.tf`
- [x] Remove ECR resource from `src/agents/test_auditor/bedrock.tf`

### 1.5 Update workflows
- [x] Delete `.github/workflows/api_shared_ecr.yml`
- [x] Update `.github/workflows/agents_workflow_fixer.yml` - Use consolidated ECR with prefixed tags
- [x] Update `.github/workflows/agents_agent_creator.yml` - Use consolidated ECR with prefixed tags
- [x] Update `.github/workflows/agents_test_auditor.yml` - No changes needed (no Docker steps)
- [x] Update ECR repo URL extraction in agent workflows
- [x] Update `etc/workflow-dependencies.yml` - Remove api_shared_ecr, update dependencies

### 1.6 Update tests
- [x] Move/update tests from `test/api/shared/ecr/` to `test/bootstrap/`
- [x] Delete `test/api/shared/ecr/` directory

---

## Phase 2: VPC & Security Group Consolidation

### 2.1 Create VPC in bootstrap
- [x] Create `src/bootstrap/vpc.tf`
- [x] Add VPC resource (CIDR: 10.0.0.0/16)
- [x] Add public subnets across AZs
- [x] Add internet gateway
- [x] Add route tables and associations

### 2.2 Create security groups in bootstrap
- [x] Add runner security group to `src/bootstrap/vpc.tf` (or separate file)

### 2.3 Update bootstrap outputs
- [x] Add `vpc_id` output
- [x] Add `vpc_public_subnet_ids` output
- [x] Add `runner_security_group_id` output

### 2.4 Update consumers
- [x] `src/api/endpoints/runners/data.tf` - Reference bootstrap for VPC
- [x] `src/api/endpoints/runners/outputs.tf` - Pass through from bootstrap
- [x] `src/api/endpoints/runners/lambda.tf` - Use bootstrap VPC ID
- [x] `src/api/endpoints/ecs_runner/data.tf` - Reference bootstrap for VPC
- [x] `src/api/endpoints/ecs_runner/lambda.tf` - Use bootstrap VPC/subnets/SG
- [x] `src/api/endpoints/ec2_runner/data.tf` - Reference bootstrap for VPC
- [x] `src/api/endpoints/ec2_runner/lambda.tf` - Use bootstrap VPC/subnets/SG

### 2.5 Remove old VPC definitions
- [x] Delete `src/api/endpoints/runners/vpc.tf` (entire file)

---

## Phase 3: S3 Bucket Reusable Module

### 3.1 Create module
- [x] Create `lib/terraform/modules/s3-bucket/main.tf`
- [x] Create `lib/terraform/modules/s3-bucket/variables.tf`
- [x] Create `lib/terraform/modules/s3-bucket/outputs.tf`

### 3.2 Update consumers
- [x] Refactor `src/api/backend/cloudfront_s3.tf` to use s3_bucket module
- [x] Refactor `src/www/shared/cloudfront_s3.tf` to use s3_bucket module

### 3.3 CloudFront WAF Module
- [x] Create `lib/terraform/modules/cloudfront_waf/` module
- [x] Refactor `src/api/backend/cloudfront_s3.tf` to use cloudfront_waf module
- [x] Refactor `src/www/shared/cloudfront_s3.tf` to use cloudfront_waf module

### 3.4 Snake_case naming cleanup
- [x] Rename `github-oidc` to `github_oidc`
- [x] Rename `webhook-lambda` to `webhook_lambda` (agents)
- [x] Rename `agent-code` to `agent_code` (agents)

---

## Phase 4: Update Dependency Graph & Final Tests

### 4.1 Update workflow dependencies
- [x] Remove `api_shared_ecr` entry from `etc/workflow-dependencies.yml`
- [x] Update `endpoint_v1_image_for_ecs_runners` to depend on `endpoint_v1_ec2_runner`
- [x] Update paths for bootstrap to include `lib/terraform/**`

### 4.2 Final verification
- [x] Run `terraform fmt -check -recursive` on all modified directories
- [ ] Run `terraform validate` on all modified directories
- [ ] Verify bootstrap workflow passes
- [ ] Verify dependent workflows pass

---

## Execution Order

1. **Phase 1.1-1.2**: Create ECR in bootstrap, add outputs
2. **Phase 2.1-2.3**: Create VPC/SG in bootstrap, add outputs
3. **Phase 3.1**: Create S3 bucket module
4. **Deploy bootstrap**: Apply terraform to create new resources
5. **Phase 1.3, 2.4, 3.2**: Update all consumers to reference bootstrap
6. **Phase 1.4, 2.5**: Remove old resource definitions
7. **Phase 1.5, 4.1**: Update workflows and dependency graph
8. **Phase 1.6, 4.2**: Update tests and final verification

---

## Risk Mitigation

1. **ECR images**: Agents use `latest` tag, runners use `latest`/`stable`. Image loss during migration is acceptable since images can be rebuilt.

2. **VPC resources**: ECS tasks will need to be drained before VPC migration. Schedule during low-traffic period.

3. **State management**: Use `terraform state mv` for resources that need to be preserved, or `terraform import` for resources that can be recreated.

4. **Rollback**: Keep old definitions commented out until verification complete.

---

## Files Changed Summary

### New Files
- `src/bootstrap/ecr.tf`
- `src/bootstrap/vpc.tf`
- `lib/terraform/modules/s3-bucket/main.tf`
- `lib/terraform/modules/s3-bucket/variables.tf`
- `lib/terraform/modules/s3-bucket/outputs.tf`

### Modified Files
- `src/bootstrap/outputs.tf`
- `src/api/endpoints/runners/data.tf`
- `src/api/endpoints/runners/outputs.tf`
- `src/api/endpoints/runners/lambda.tf`
- `src/api/endpoints/runners/vpc.tf`
- `src/api/endpoints/ecs_runner/data.tf`
- `src/api/endpoints/ecs_runner/ecs.tf`
- `src/api/endpoints/ec2_runner/lambda.tf`
- `src/api/endpoints/image_for_ecs_runners/locals.tf`
- `src/agents/agent_creator/agentcore.tf`
- `src/agents/agent_creator/locals.tf`
- `src/agents/agent_creator/iam.tf`
- `src/agents/workflow_fixer/agentcore.tf`
- `src/agents/workflow_fixer/locals.tf`
- `src/agents/workflow_fixer/iam.tf`
- `src/agents/test_auditor/bedrock.tf`
- `src/agents/test_auditor/locals.tf`
- `src/agents/test_auditor/iam.tf`
- `src/api/backend/cloudfront_s3.tf`
- `src/www/shared/cloudfront_s3.tf`
- `.github/workflows/bootstrap.yml`
- `.github/workflows/agents_workflow_fixer.yml`
- `.github/workflows/agents_agent_creator.yml`
- `.github/workflows/agents_test_auditor.yml`
- `etc/workflow-dependencies.yml`

### Deleted Files
- `src/api/shared/ecr/` (entire directory)
- `src/agents/agent_creator/ecr.tf`
- `src/agents/workflow_fixer/ecr.tf`
- `.github/workflows/api_shared_ecr.yml`
- `test/api/shared/ecr/` (entire directory)
