# Infrastructure Modernization and RTL Simulation Platform

## Table of Contents

- [Goal](#goal)
- [Testing Standards](#testing-standards)
- [Architecture Decisions](#architecture-decisions)
- [Task List](#task-list)
  - [Phase 1: Region Migration](#phase-1-region-migration-us-east-1--us-east-2)
  - [Phase 2: Workflow Ordering System](#phase-2-workflow-ordering-system)
  - [Phase 3: Runner Label System Refactor](#phase-3-runner-label-system-refactor)
  - [Phase 4: EC2 Infrastructure Foundation](#phase-4-ec2-infrastructure-foundation-for-rtl)
  - [Phase 5: RTL Runner AMIs](#phase-5-rtl-runner-amis)
  - [Phase 6: EC2 Launch Templates and Scaling](#phase-6-ec2-launch-templates-and-scaling)
  - [Phase 7: RTL Simulation Endpoint](#phase-7-rtl-simulation-endpoint)
  - [Phase 8: Tri-Mode Core Development](#phase-8-tri-mode-core-development)
  - [Phase 9: RTL Synthesis Pipeline](#phase-9-rtl-synthesis-pipeline)
  - [Phase 10: Frontend Updates](#phase-10-frontend-updates)
  - [Phase 11: Fabrication Preparation](#phase-11-fabrication-preparation)
- [File Changes Summary](#file-changes-summary)
- [References](#references)

---

## Goal

Build a real, cycle-accurate RTL simulation platform for a tri-mode RISC-V SoC that can eventually be fabricated via ChipFoundry.io. This requires modernizing the runner infrastructure to support compute-intensive workloads (Verilator simulation, OpenLane synthesis) alongside existing CI/CD workflows.

### Key Outcomes

1. **Region Migration**: Move all infrastructure from us-east-1 to us-east-2 for consistency and instance availability (c8i, r8i, g6e all available).

2. **Workflow Orchestration**: Implement proper workflow ordering so dependent workflows deploy in sequence, while independent workflows deploy in parallel.

3. **Runner Label System**: Replace monolithic labels (`ecs-fargate`) with composable labels (`ecs`, `fargate`, `spot`) that combine to select the appropriate runner.

4. **RTL Runners**: Add specialized runners for RTL simulation (Chipyard/Verilator) and synthesis (OpenLane/SKY130).

5. **Fabrication Path**: Establish a path from RTL → GDSII → physical chip via ChipFoundry.io (US company, credit card, no license fees).

---

## Testing Standards

All code must follow the testing pyramid as defined in CLAUDE.md:

```
        /\
       /  \      E2E Tests (few)
      /----\     - Full workflow runs
     /      \    - Cross-service integration
    /--------\   Integration Tests (some)
   /          \  - AWS service interactions
  /------------\ - API endpoint behavior
 /              \
/----------------\ Unit Tests (many)
                   - Pure functions
                   - Business logic
                   - Input validation
                   - Error handling
```

### Testing Principles

1. **Unit tests > Integration tests > E2E tests** - Most problems must be caught by unit tests
2. **Full test coverage** - Every function, every branch
3. **Atomic tests** - Each test verifies one thing
4. **Single responsibility** - One assertion per test (or logically grouped assertions)
5. **Unit tests for everything** except functionality that explicitly requires integration or e2e flows

### Test Directory Structure

```
test/
├── api/
│   └── endpoints/
│       ├── runners/
│       │   ├── pre_deployment/     # Unit tests (run before deploy)
│       │   │   ├── test_label_parsing.py
│       │   │   ├── test_instance_selection.py
│       │   │   └── test_validation.py
│       │   └── post_deployment/
│       │       ├── integration/    # Integration tests (after deploy)
│       │       │   └── test_runner_api.py
│       │       └── e2e/            # E2E tests (full workflow)
│       │           └── test_runner_lifecycle.py
│       ├── rtl_simulation/
│       │   ├── pre_deployment/
│       │   └── post_deployment/
│       └── rtl_synthesis/
│           ├── pre_deployment/
│           └── post_deployment/
└── lib/
    └── test_workflow_ordering.py
```

---

## Architecture Decisions

### Instance Types (Intel i-series for cache performance)

| Runner Type | Instance | vCPU | RAM | Use Case |
|-------------|----------|------|-----|----------|
| General CI/CD | ECS Fargate | 4 | 8 GB | Linting, testing, Terraform |
| RTL Simulation | c8i.4xlarge | 16 | 32 GB | Verilator builds and runs |
| RTL Synthesis | r8i.4xlarge | 16 | 128 GB | OpenLane/Yosys (memory-bound) |
| GPU Acceleration | g6e.xlarge | 4 | 16 GB + L40S | RTLflow batch simulation |

**Why Intel (i) over AMD (a)?** The c8i/r8i have 4.6x larger L3 cache per core than previous generations. Verilator is cache-bound, so more cache = faster simulation.

**Why On-Demand over Spot?** RTL builds take hours. Spot interruption would lose significant work. On-Demand for builds; Spot only for parallelizable batch runs.

### Runner Label System

Labels combine to select runners:

```
Platform:     ecs | ec2
Compute:      fargate | c8i | r8i | g6e
Pricing:      spot | on-demand
Workflow ID:  runner-{github.run_id}
```

Examples:
- `["ecs", "fargate", "spot", "runner-12345"]` → ECS Fargate Spot
- `["ec2", "c8i", "on-demand", "runner-12345"]` → EC2 c8i.4xlarge On-Demand
- `["ec2", "r8i", "on-demand", "runner-12345"]` → EC2 r8i.4xlarge On-Demand
- `["ec2", "g6e", "on-demand", "runner-12345"]` → EC2 g6e.xlarge On-Demand

### Workflow Deployment Order

```
Level 0: bootstrap.yml (foundation - IAM, S3, Route53)
    ↓
Level 1: ecr.yml, www_shared.yml (shared resources)
    ↓
Level 2: runners.yml, api.yml (runner infra, API Gateway)
    ↓
Level 3: image_for_ecs_runners.yml, image_for_ec2_runners_*.yml (runner images)
    ↓
Level 4: ecs_runner.yml, ec2_runner.yml (runner endpoints)
    ↓
Level 5: All other endpoints (health, echo, contact, rack_designer, simulation_soc, etc.)
```

When a commit affects multiple levels, workflows must deploy in order. When a commit affects only one workflow, it deploys independently.

### GitOps and Bootstrap Resources

**Principle**: All infrastructure must be reproducible from zero without human intervention.

When bootstrapping (chicken-and-egg problems):
1. **Initial creation via CLI is acceptable** for truly foundational resources (S3 state bucket, bootstrap IAM)
2. **Terraform must track these resources afterward** via import or data sources
3. **Subsequent deployments must be fully automated** through CI/CD workflows

Resources that require bootstrapping:
- S3 bucket for Terraform state (created via CLI, then managed by `src/bootstrap/state.tf`)
- S3 bucket for central logs (created via CLI, then managed by `src/bootstrap/central_logs.tf`)
- OIDC provider for GitHub Actions (managed by `src/bootstrap/oidc.tf`)

**Integration Test Race Conditions**: Tests must handle resource availability:
- Use retry logic with exponential backoff for eventual consistency
- Check resource existence before testing dependent functionality
- Tests must pass when run repeatedly from a clean state

### Simulation Acceleration Strategy

| Method | Speedup | Status |
|--------|---------|--------|
| Checkpointing | 10-100x (skip boot) | Implement now |
| GPU Batch (RTLflow) | 100x throughput | Implement now |
| FPGA (FireSim) | 1000x | Blocked until FireSim supports F2 |

AWS F1 instances are deprecated (EOL December 31, 2025) and unavailable to new users.
FireSim F2 support is in development. Monitor: https://github.com/firesim/firesim

---

## Task List

### Phase 1: Region Migration (us-east-1 → us-east-2)

#### 1.1 Infrastructure Changes
- [x] 1.1.1. Update `lib/terraform/outputs.tf` to change `aws_region` from `us-east-1` to `us-east-2`
- [x] 1.1.2. Create new S3 bucket for Terraform state in us-east-2
- [x] 1.1.3. Create new S3 bucket for central logs in us-east-2
- [x] 1.1.4. Migrate Route53 hosted zone (global, no region change needed)
- [x] 1.1.5. Update bootstrap Terraform to target us-east-2
- [x] 1.1.6. Run bootstrap in us-east-2 to create IAM roles, OIDC provider
- [x] 1.1.7. Update ECR repository to us-east-2 (or use ECR replication)
- [x] 1.1.8. Update all workflow files to reference us-east-2
- [x] 1.1.9. Update all Terraform backend configs to use new state bucket
- [ ] 1.1.10. Migrate existing infrastructure (destroy us-east-1, apply us-east-2)
- [ ] 1.1.11. Update DNS records if any reference regional endpoints
- [ ] 1.1.12. Verify all endpoints functional in us-east-2
- [ ] 1.1.13. Decommission us-east-1 resources

#### 1.2 Unit Tests for Region Migration
- [ ] 1.2.1. Test `lib/terraform/outputs.tf` parsing returns correct region
- [ ] 1.2.2. Test workflow region extraction logic
- [ ] 1.2.3. Test backend config region validation
- [ ] 1.2.4. Test ARN construction with new region

#### 1.3 Integration Tests for Region Migration
- [ ] 1.3.1. Test S3 bucket accessibility in us-east-2
- [ ] 1.3.2. Test IAM role assumption in us-east-2
- [ ] 1.3.3. Test ECR image pull from us-east-2

#### 1.4 E2E Tests for Region Migration
- [ ] 1.4.1. Run full workflow on us-east-2 infrastructure
- [ ] 1.4.2. Verify API endpoints respond from us-east-2

### Phase 2: Workflow Ordering System

#### 2.1 Design and Implementation
- [x] 2.1.1. Create `.github/workflow-order.yml` defining workflow dependency graph
- [x] 2.1.2. Create `lib/workflow_ordering.py` module with:
  - `parse_workflow_order(yaml_path)` - parse dependency graph
  - `get_affected_workflows(changed_files)` - determine affected workflows
  - `get_deployment_order(affected)` - topological sort for order
  - `should_wait_for(workflow, completed)` - check if dependencies met
- [x] 2.1.3. Create reusable workflow `.github/workflows/check-dependencies.yml`
- [x] 2.1.4. Add `workflow_call` triggers to all workflows for orchestration
- [x] 2.1.5. Create orchestrator workflow that triggers workflows in correct order
- [x] 2.1.6. Update each workflow to check dependencies before running

#### 2.2 Unit Tests for Workflow Ordering
- [x] 2.2.1. Test `parse_workflow_order` with valid YAML
- [x] 2.2.2. Test `parse_workflow_order` with invalid YAML (error handling)
- [x] 2.2.3. Test `parse_workflow_order` with circular dependencies (error)
- [x] 2.2.4. Test `get_affected_workflows` with single file change
- [x] 2.2.5. Test `get_affected_workflows` with multiple file changes
- [x] 2.2.6. Test `get_affected_workflows` with no matching workflows
- [x] 2.2.7. Test `get_deployment_order` returns correct topological order
- [x] 2.2.8. Test `get_deployment_order` with single workflow (no deps)
- [x] 2.2.9. Test `get_deployment_order` with diamond dependency
- [x] 2.2.10. Test `should_wait_for` with all deps complete
- [x] 2.2.11. Test `should_wait_for` with missing deps
- [x] 2.2.12. Test `should_wait_for` with no deps

#### 2.3 Integration Tests for Workflow Ordering
- [ ] 2.3.1. Test workflow trigger via GitHub API (requires CI environment)
- [ ] 2.3.2. Test workflow status polling (requires CI environment)

#### 2.4 Documentation
- [x] 2.4.1. Document workflow ordering system (see `docs/workflow-ordering.md`)

### Phase 3: Runner Label System Refactor

#### 3.1 Label Schema Design
- [x] 3.1.1. Update `etc/runners.yml` with new label schema:
  ```yaml
  labels:
    platform:
      - ecs
      - ec2
    compute:
      - fargate
      - c8i
      - r8i
      - g6e
    pricing:
      - spot
      - on-demand
  instance_types:
    c8i: c8i.4xlarge
    r8i: r8i.4xlarge
    g6e: g6e.xlarge
  ```

#### 3.2 Label Parsing Implementation
- [x] 3.2.1. Create `lib/runner_labels.py` module with:
  - `parse_labels(label_list)` - extract platform, compute, pricing, runner_id
  - `validate_labels(parsed)` - check valid combinations
  - `get_instance_type(parsed)` - return EC2 instance type
  - `get_ecs_config(parsed)` - return ECS task config
  - `is_spot(parsed)` - check if spot pricing
- [x] 3.2.2. Update runner Lambda to use new label parsing
- [x] 3.2.3. Create label-to-instance-type mapping in `src/api/endpoints/runners/locals.tf`
- [x] 3.2.4. Update ECS task definitions to support label-based selection (uses FARGATE_SPOT for spot labels)
- [x] 3.2.5. Update EC2 launch logic to select instance type based on labels
- [x] 3.2.6. Update webhook router to use new label format (with legacy fallback)
- [x] 3.2.7. Update runner registration to apply all labels
- [x] 3.2.8. Add validation to reject invalid label combinations (via parse_labels/validate_labels)

#### 3.3 Unit Tests for Label System
- [x] 3.3.1. Test `parse_labels` with valid ECS labels
- [x] 3.3.2. Test `parse_labels` with valid EC2 labels
- [x] 3.3.3. Test `parse_labels` with missing platform (error)
- [x] 3.3.4. Test `parse_labels` with missing compute (error)
- [x] 3.3.5. Test `parse_labels` extracts runner_id correctly
- [x] 3.3.6. Test `parse_labels` with no runner_id (error)
- [x] 3.3.7. Test `validate_labels` accepts ecs+fargate+spot
- [x] 3.3.8. Test `validate_labels` accepts ecs+fargate+on-demand
- [x] 3.3.9. Test `validate_labels` accepts ec2+c8i+on-demand
- [x] 3.3.10. Test `validate_labels` accepts ec2+r8i+on-demand
- [x] 3.3.11. Test `validate_labels` accepts ec2+g6e+on-demand
- [x] 3.3.12. Test `validate_labels` rejects ecs+c8i (invalid combo)
- [x] 3.3.13. Test `validate_labels` rejects ec2+fargate (invalid combo)
- [x] 3.3.14. Test `get_instance_type` returns c8i.4xlarge for c8i
- [x] 3.3.15. Test `get_instance_type` returns r8i.4xlarge for r8i
- [x] 3.3.16. Test `get_instance_type` returns g6e.xlarge for g6e
- [x] 3.3.17. Test `get_instance_type` returns None for fargate
- [x] 3.3.18. Test `get_ecs_config` returns correct CPU/memory for fargate
- [x] 3.3.19. Test `is_spot` returns True for spot label
- [x] 3.3.20. Test `is_spot` returns False for on-demand label

#### 3.4 Integration Tests for Label System
- [x] 3.4.1. Test runner API accepts new label format (see `test_label_system.py`)
- [x] 3.4.2. Test ECS task launches with correct config (label validation tests)
- [x] 3.4.3. Test EC2 instance launches with correct type (label validation tests)

#### 3.5 E2E Tests for Label System
- [ ] 3.5.1. Test full workflow with ECS Fargate runner
- [ ] 3.5.2. Test full workflow with EC2 c8i runner

#### 3.6 Documentation
- [x] 3.6.1. Document label system (see `docs/runner-labels.md`)

### Phase 4: EC2 Infrastructure Foundation for RTL

> **Architecture Decision**: RTL runners use EC2 with custom AMIs (not Docker/ECS) because:
> - GPU support required (Fargate has none)
> - Memory needs exceed Fargate limits (128GB for synthesis)
> - Cache-bound Verilator benefits from bare-metal performance
> - Long-running jobs (hours) without container overhead

#### 4.1 IAM Roles
- [ ] 4.1.1. Create IAM role for Packer (EC2 + AMI creation permissions)
- [ ] 4.1.2. Create IAM role for RTL runners (S3, CloudWatch, SSM access)
- [ ] 4.1.3. Create instance profile for RTL runners

#### 4.2 Security Groups
- [ ] 4.2.1. Create security group for Packer build instances
- [ ] 4.2.2. Create security group for RTL runners (egress only, no ingress)

#### 4.3 VPC Configuration
- [ ] 4.3.1. Verify VPC has subnets in availability zones with c8i, r8i, g6e capacity
- [ ] 4.3.2. Ensure NAT gateway for private subnet egress (GitHub API access)

#### 4.4 Terraform
- [ ] 4.4.1. Create `src/api/endpoints/rtl_runner/` directory
- [ ] 4.4.2. Create Terraform for IAM roles and policies
- [ ] 4.4.3. Create Terraform for security groups
- [ ] 4.4.4. Create GitHub workflow `rtl_runner.yml` for infrastructure

#### 4.5 Unit Tests for Infrastructure
- [ ] 4.5.1. Test IAM policy document construction
- [ ] 4.5.2. Test security group rule validation
- [ ] 4.5.3. Test instance type validation (c8i, r8i, g6e only)

#### 4.6 Integration Tests for Infrastructure
- [ ] 4.6.1. Test IAM role assumption
- [ ] 4.6.2. Test security group allows required egress

### Phase 5: RTL Runner AMIs

#### 5.1 Directory Structure
- [x] 5.1.1. Create `src/api/endpoints/ami_for_rtl_runners/` directory
- [ ] 5.1.2. Create `src/api/endpoints/ami_for_rtl_runners/packer/` directory
- [ ] 5.1.3. Create `src/api/endpoints/ami_for_rtl_runners/scripts/` directory

#### 5.2 Configuration Files
- [x] 5.2.1. Create `config/rtl-sim.yml` (instance config for c8i.4xlarge)
- [x] 5.2.2. Create `config/rtl-synth.yml` (instance config for r8i.4xlarge)
- [x] 5.2.3. Create `config/rtl-gpu.yml` (instance config for g6e.xlarge)

#### 5.3 Packer Templates
- [ ] 5.3.1. Create `packer/rtl-sim.pkr.hcl`:
  - Base: Ubuntu 24.04 AMI
  - Install: Verilator 5.024, Chipyard 1.11.0, RISC-V toolchain
  - Install: GitHub Actions runner
  - Configure: Environment variables, paths
- [ ] 5.3.2. Create `packer/rtl-synth.pkr.hcl`:
  - Base: Ubuntu 24.04 AMI
  - Install: OpenLane 2.1.0, SKY130 PDK, Yosys, Magic, KLayout
  - Install: GitHub Actions runner
- [ ] 5.3.3. Create `packer/rtl-gpu.pkr.hcl`:
  - Base: NVIDIA CUDA Ubuntu 24.04 AMI
  - Install: CUDA 12.4, RTLflow, Verilator
  - Install: GitHub Actions runner

#### 5.4 Provisioning Scripts
- [ ] 5.4.1. Create `scripts/install-runner.sh` (GitHub Actions runner setup)
- [ ] 5.4.2. Create `scripts/install-verilator.sh`
- [ ] 5.4.3. Create `scripts/install-chipyard.sh`
- [ ] 5.4.4. Create `scripts/install-openlane.sh`
- [ ] 5.4.5. Create `scripts/install-rtlflow.sh`

#### 5.5 Build Workflow
- [ ] 5.5.1. Create GitHub workflow `ami_for_rtl_runners.yml`
- [ ] 5.5.2. Add AMI tagging and versioning
- [ ] 5.5.3. Add AMI cleanup (delete old versions)

#### 5.6 Unit Tests for RTL AMIs
- [x] 5.6.1. Test config YAML parsing for rtl-sim
- [x] 5.6.2. Test config YAML parsing for rtl-synth
- [x] 5.6.3. Test config YAML parsing for rtl-gpu
- [ ] 5.6.4. Test Packer template validation (packer validate)
- [ ] 5.6.5. Test provisioning script syntax (shellcheck)

#### 5.7 Integration Tests for RTL AMIs
- [ ] 5.7.1. Test AMI builds successfully
- [ ] 5.7.2. Test AMI boots and tools are available
- [ ] 5.7.3. Test runner registration works

#### 5.8 Documentation
- [ ] 5.8.1. Document RTL AMI build process

### Phase 6: EC2 Launch Templates and Scaling

#### 6.1 Launch Templates
- [ ] 6.1.1. Create launch template `rtl-sim-c8i`:
  - Instance type: c8i.4xlarge
  - AMI: RTL sim AMI from Phase 5
  - Storage: 100 GB gp3
  - User data: Runner registration script
- [ ] 6.1.2. Create launch template `rtl-synth-r8i`:
  - Instance type: r8i.4xlarge
  - AMI: RTL synth AMI from Phase 5
  - Storage: 200 GB gp3
- [ ] 6.1.3. Create launch template `rtl-gpu-g6e`:
  - Instance type: g6e.xlarge
  - AMI: RTL GPU AMI from Phase 5
  - Storage: 100 GB gp3

#### 6.2 Scaling and Lifecycle
- [ ] 6.2.1. Update ec2_runner Lambda to support RTL instance types
- [ ] 6.2.2. Add CloudWatch metrics for RTL runner utilization
- [ ] 6.2.3. Add cost allocation tags

#### 6.3 Unit Tests for Launch Templates
- [ ] 6.3.1. Test launch template generation
- [ ] 6.3.2. Test user data script construction
- [ ] 6.3.3. Test cost tag generation

#### 6.4 Integration Tests for EC2 Runners
- [ ] 6.4.1. Test EC2 instance launch with RTL AMI
- [ ] 6.4.2. Test runner registration with GitHub
- [ ] 6.4.3. Test runner termination on job complete

#### 6.5 E2E Tests for RTL Runners
- [ ] 6.5.1. Test full RTL simulation job on c8i
- [ ] 6.5.2. Test full RTL synthesis job on r8i

### Phase 7: RTL Simulation Endpoint

#### 7.1 API Design
- [ ] 7.1.1. Create `src/api/endpoints/rtl_simulation/` directory
- [ ] 7.1.2. Create API Lambda handler with endpoints:
  - `POST /v1/rtl-simulation` - Submit simulation job
  - `GET /v1/rtl-simulation/{job_id}` - Get job status
  - `GET /v1/rtl-simulation/{job_id}/results` - Get results
- [ ] 7.1.3. Create DynamoDB table for job tracking
- [ ] 7.1.4. Create S3 bucket for simulation artifacts

#### 7.2 Simulation Runner
- [ ] 7.2.1. Create simulation runner script:
  - Clone/update Chipyard
  - Build BOOM with tri-mode modifications
  - Run Verilator simulation
  - Upload results to S3
  - Update job status in DynamoDB
- [ ] 7.2.2. Add job timeout and cleanup
- [ ] 7.2.3. Add cost tracking per job

#### 7.3 Unit Tests for RTL Simulation
- [ ] 7.3.1. Test job submission validation
- [ ] 7.3.2. Test job ID generation
- [ ] 7.3.3. Test job status state machine
- [ ] 7.3.4. Test persona validation (riscv, desktop64, mobile64)
- [ ] 7.3.5. Test workload parameter validation
- [ ] 7.3.6. Test S3 artifact path generation
- [ ] 7.3.7. Test DynamoDB item construction
- [ ] 7.3.8. Test cost calculation logic
- [ ] 7.3.9. Test timeout detection
- [ ] 7.3.10. Test error response formatting

#### 7.4 Integration Tests for RTL Simulation
- [ ] 7.4.1. Test job submission to API
- [ ] 7.4.2. Test job status retrieval
- [ ] 7.4.3. Test S3 artifact upload/download
- [ ] 7.4.4. Test DynamoDB read/write

#### 7.5 E2E Tests for RTL Simulation
- [ ] 7.5.1. Test full simulation workflow (submit → poll → results)

#### 7.6 Frontend Updates
- [ ] 7.6.1. Update simulation UI to trigger real RTL simulations
- [ ] 7.6.2. Add job queue visualization
- [ ] 7.6.3. Add simulation progress tracking

### Phase 8: Tri-Mode Core Development

#### 8.1 Repository Setup
- [ ] 8.1.1. Fork Chipyard repository to 10U-Labs-LLC GitHub
- [ ] 8.1.2. Create branch for tri-mode modifications
- [ ] 8.1.3. Study BOOM frontend decode stage implementation

#### 8.2 Tri-Mode Decode Architecture
- [ ] 8.2.1. Design mode detection from instruction stream
- [ ] 8.2.2. Design Desktop64 decode lane
- [ ] 8.2.3. Design Mobile64 decode lane
- [ ] 8.2.4. Design unified micro-op emission to backend

#### 8.3 Implementation
- [ ] 8.3.1. Implement mode switching logic
- [ ] 8.3.2. Implement Desktop64 decoder stub
- [ ] 8.3.3. Implement Mobile64 decoder stub
- [ ] 8.3.4. Implement micro-op translation tables
- [ ] 8.3.5. Add flags speculation hardware
- [ ] 8.3.6. Add hardware TSO mode for Desktop64

#### 8.4 Unit Tests for Tri-Mode Core
- [ ] 8.4.1. Test mode detection logic
- [ ] 8.4.2. Test Desktop64 instruction decode
- [ ] 8.4.3. Test Mobile64 instruction decode
- [ ] 8.4.4. Test micro-op emission format
- [ ] 8.4.5. Test flags speculation hit/miss
- [ ] 8.4.6. Test TSO mode memory ordering

#### 8.5 Integration Tests for Tri-Mode Core
- [ ] 8.5.1. Run RISC-V compliance tests (native mode)
- [ ] 8.5.2. Measure IPC overhead vs. baseline BOOM

#### 8.6 Documentation
- [ ] 8.6.1. Document tri-mode architecture

### Phase 9: RTL Synthesis Pipeline

#### 9.1 API Design
- [ ] 9.1.1. Create `src/api/endpoints/rtl_synthesis/` directory
- [ ] 9.1.2. Create synthesis job API endpoint
- [ ] 9.1.3. Create synthesis job tracking in DynamoDB

#### 9.2 Synthesis Runner
- [ ] 9.2.1. Create synthesis runner script:
  - Take Verilog from simulation output
  - Run OpenLane flow
  - Generate timing/area reports
  - Generate GDSII
  - Upload artifacts to S3
- [ ] 9.2.2. Add DRC/LVS verification step

#### 9.3 Unit Tests for RTL Synthesis
- [ ] 9.3.1. Test synthesis job validation
- [ ] 9.3.2. Test Verilog input validation
- [ ] 9.3.3. Test OpenLane config generation
- [ ] 9.3.4. Test timing report parsing
- [ ] 9.3.5. Test area report parsing
- [ ] 9.3.6. Test DRC result parsing

#### 9.4 Integration Tests for RTL Synthesis
- [ ] 9.4.1. Test synthesis job submission
- [ ] 9.4.2. Test GDSII artifact download

#### 9.5 Frontend and Documentation
- [ ] 9.5.1. Create synthesis results dashboard
- [ ] 9.5.2. Document synthesis pipeline

### Phase 10: Frontend Updates

- [ ] 10.1. Update simulation UI to trigger real RTL simulations
- [ ] 10.2. Add job queue visualization
- [ ] 10.3. Add simulation progress tracking
- [ ] 10.4. Add waveform viewer (load VCD from S3)
- [ ] 10.5. Add synthesis results visualization
- [ ] 10.6. Add cost tracking display
- [ ] 10.7. Add architecture documentation pages
- [ ] 10.8. Add fabrication path documentation

### Phase 11: Fabrication Preparation

- [ ] 11.1. Research ChipFoundry.io submission requirements
- [ ] 11.2. Create GDSII validation pipeline
- [ ] 11.3. Create design rule check automation
- [ ] 11.4. Create submission package generator
- [ ] 11.5. Document fabrication process
- [ ] 11.6. Estimate fabrication cost and timeline
- [ ] 11.7. Create fabrication checklist

---

## File Changes Summary

### New Files

```
TODO.md (this file)
.github/workflow-order.yml
.github/workflows/check-dependencies.yml
.github/workflows/orchestrator.yml
.github/workflows/rtl_simulation.yml
.github/workflows/rtl_synthesis.yml
.github/workflows/image_for_rtl_runners.yml
lib/workflow_ordering.py
lib/runner_labels.py
src/api/endpoints/rtl_simulation/
src/api/endpoints/rtl_synthesis/
src/api/endpoints/image_for_rtl_runners/
src/api/endpoints/image_for_rtl_runners/config/rtl-sim.yml
src/api/endpoints/image_for_rtl_runners/config/rtl-synth.yml
src/api/endpoints/image_for_rtl_runners/config/rtl-gpu.yml
src/api/endpoints/image_for_rtl_runners/dockerfiles/Dockerfile.sim
src/api/endpoints/image_for_rtl_runners/dockerfiles/Dockerfile.synth
src/api/endpoints/image_for_rtl_runners/dockerfiles/Dockerfile.gpu
test/lib/test_workflow_ordering.py
test/lib/test_runner_labels.py
test/api/endpoints/rtl_simulation/
test/api/endpoints/rtl_synthesis/
```

### Modified Files

```
lib/terraform/outputs.tf (region change)
etc/runners.yml (new label schema)
src/bootstrap/*.tf (region change)
src/api/endpoints/runners/ (label system refactor)
src/api/endpoints/simulation_soc/ (replace analytical model)
src/www/paths/simulations/soc/ (frontend updates)
.github/workflows/*.yml (all workflows - region, labels, ordering)
```

---

## References

- [Chipyard Documentation](https://chipyard.readthedocs.io/)
- [BOOM Documentation](https://docs.boom-core.org/)
- [OpenLane Documentation](https://openlane.readthedocs.io/)
- [SKY130 PDK](https://github.com/google/skywater-pdk)
- [ChipFoundry.io](https://chipfoundry.io/)
- [RTLflow (GPU acceleration)](https://github.com/dian-lun-lin/RTLflow)
- [AWS EC2 c8i](https://aws.amazon.com/ec2/instance-types/c8i/)
- [AWS EC2 r8i](https://aws.amazon.com/ec2/instance-types/r8i/)
- [AWS EC2 g6e](https://aws.amazon.com/ec2/instance-types/g6e/)
