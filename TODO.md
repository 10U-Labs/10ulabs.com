# Infrastructure Modernization and RTL Simulation Platform

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

---

## Task List

### Phase 1: Region Migration (us-east-1 → us-east-2)

#### 1.1 Infrastructure Changes
- [ ] 1.1.1. Update `lib/terraform/outputs.tf` to change `aws_region` from `us-east-1` to `us-east-2`
- [ ] 1.1.2. Create new S3 bucket for Terraform state in us-east-2
- [ ] 1.1.3. Create new S3 bucket for central logs in us-east-2
- [ ] 1.1.4. Migrate Route53 hosted zone (global, no region change needed)
- [ ] 1.1.5. Update bootstrap Terraform to target us-east-2
- [ ] 1.1.6. Run bootstrap in us-east-2 to create IAM roles, OIDC provider
- [ ] 1.1.7. Update ECR repository to us-east-2 (or use ECR replication)
- [ ] 1.1.8. Update all workflow files to reference us-east-2
- [ ] 1.1.9. Update all Terraform backend configs to use new state bucket
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
- [ ] 2.1.1. Create `.github/workflow-order.yml` defining workflow dependency graph
- [ ] 2.1.2. Create `lib/workflow_ordering.py` module with:
  - `parse_workflow_order(yaml_path)` - parse dependency graph
  - `get_affected_workflows(changed_files)` - determine affected workflows
  - `get_deployment_order(affected)` - topological sort for order
  - `should_wait_for(workflow, completed)` - check if dependencies met
- [ ] 2.1.3. Create reusable workflow `.github/workflows/check-dependencies.yml`
- [ ] 2.1.4. Add `workflow_call` triggers to all workflows for orchestration
- [ ] 2.1.5. Create orchestrator workflow that triggers workflows in correct order
- [ ] 2.1.6. Update each workflow to check dependencies before running

#### 2.2 Unit Tests for Workflow Ordering
- [ ] 2.2.1. Test `parse_workflow_order` with valid YAML
- [ ] 2.2.2. Test `parse_workflow_order` with invalid YAML (error handling)
- [ ] 2.2.3. Test `parse_workflow_order` with circular dependencies (error)
- [ ] 2.2.4. Test `get_affected_workflows` with single file change
- [ ] 2.2.5. Test `get_affected_workflows` with multiple file changes
- [ ] 2.2.6. Test `get_affected_workflows` with no matching workflows
- [ ] 2.2.7. Test `get_deployment_order` returns correct topological order
- [ ] 2.2.8. Test `get_deployment_order` with single workflow (no deps)
- [ ] 2.2.9. Test `get_deployment_order` with diamond dependency
- [ ] 2.2.10. Test `should_wait_for` with all deps complete
- [ ] 2.2.11. Test `should_wait_for` with missing deps
- [ ] 2.2.12. Test `should_wait_for` with no deps

#### 2.3 Integration Tests for Workflow Ordering
- [ ] 2.3.1. Test workflow trigger via GitHub API
- [ ] 2.3.2. Test workflow status polling

#### 2.4 Documentation
- [ ] 2.4.1. Document workflow ordering system in README

### Phase 3: Runner Label System Refactor

#### 3.1 Label Schema Design
- [ ] 3.1.1. Update `etc/runners.yml` with new label schema:
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
- [ ] 3.2.1. Create `lib/runner_labels.py` module with:
  - `parse_labels(label_list)` - extract platform, compute, pricing, runner_id
  - `validate_labels(parsed)` - check valid combinations
  - `get_instance_type(parsed)` - return EC2 instance type
  - `get_ecs_config(parsed)` - return ECS task config
  - `is_spot(parsed)` - check if spot pricing
- [ ] 3.2.2. Update runner Lambda to use new label parsing
- [ ] 3.2.3. Create label-to-instance-type mapping in `src/api/endpoints/runners/locals.tf`
- [ ] 3.2.4. Update ECS task definitions to support label-based selection
- [ ] 3.2.5. Update EC2 launch logic to select instance type based on labels
- [ ] 3.2.6. Update all workflows to use new label format
- [ ] 3.2.7. Update runner registration to apply all labels
- [ ] 3.2.8. Add validation to reject invalid label combinations

#### 3.3 Unit Tests for Label System
- [ ] 3.3.1. Test `parse_labels` with valid ECS labels
- [ ] 3.3.2. Test `parse_labels` with valid EC2 labels
- [ ] 3.3.3. Test `parse_labels` with missing platform (error)
- [ ] 3.3.4. Test `parse_labels` with missing compute (error)
- [ ] 3.3.5. Test `parse_labels` extracts runner_id correctly
- [ ] 3.3.6. Test `parse_labels` with no runner_id (error)
- [ ] 3.3.7. Test `validate_labels` accepts ecs+fargate+spot
- [ ] 3.3.8. Test `validate_labels` accepts ecs+fargate+on-demand
- [ ] 3.3.9. Test `validate_labels` accepts ec2+c8i+on-demand
- [ ] 3.3.10. Test `validate_labels` accepts ec2+r8i+on-demand
- [ ] 3.3.11. Test `validate_labels` accepts ec2+g6e+on-demand
- [ ] 3.3.12. Test `validate_labels` rejects ecs+c8i (invalid combo)
- [ ] 3.3.13. Test `validate_labels` rejects ec2+fargate (invalid combo)
- [ ] 3.3.14. Test `get_instance_type` returns c8i.4xlarge for c8i
- [ ] 3.3.15. Test `get_instance_type` returns r8i.4xlarge for r8i
- [ ] 3.3.16. Test `get_instance_type` returns g6e.xlarge for g6e
- [ ] 3.3.17. Test `get_instance_type` returns None for fargate
- [ ] 3.3.18. Test `get_ecs_config` returns correct CPU/memory for fargate
- [ ] 3.3.19. Test `is_spot` returns True for spot label
- [ ] 3.3.20. Test `is_spot` returns False for on-demand label

#### 3.4 Integration Tests for Label System
- [ ] 3.4.1. Test runner API accepts new label format
- [ ] 3.4.2. Test ECS task launches with correct config
- [ ] 3.4.3. Test EC2 instance launches with correct type

#### 3.5 E2E Tests for Label System
- [ ] 3.5.1. Test full workflow with ECS Fargate runner
- [ ] 3.5.2. Test full workflow with EC2 c8i runner

#### 3.6 Documentation
- [ ] 3.6.1. Document label system in README

### Phase 4: RTL Runner Images

#### 4.1 Directory Structure
- [ ] 4.1.1. Create `src/api/endpoints/image_for_rtl_runners/` directory
- [ ] 4.1.2. Create `src/api/endpoints/image_for_rtl_runners/config/` directory
- [ ] 4.1.3. Create `src/api/endpoints/image_for_rtl_runners/dockerfiles/` directory

#### 4.2 Configuration Files
- [ ] 4.2.1. Create `config/rtl-sim.yml`:
  ```yaml
  runner_user: "github-runner"
  runner_version: "2.330.0"
  instance_type: c8i.4xlarge
  ami_base: ubuntu-24.04-amd64
  disk_size_gb: 100
  chipyard_version: "1.11.0"
  verilator_version: "5.024"
  ```
- [ ] 4.2.2. Create `config/rtl-synth.yml`:
  ```yaml
  runner_user: "github-runner"
  runner_version: "2.330.0"
  instance_type: r8i.4xlarge
  ami_base: ubuntu-24.04-amd64
  disk_size_gb: 200
  openlane_version: "2.1.0"
  sky130_pdk_version: "1.0.457"
  ```
- [ ] 4.2.3. Create `config/rtl-gpu.yml`:
  ```yaml
  runner_user: "github-runner"
  runner_version: "2.330.0"
  instance_type: g6e.xlarge
  ami_base: nvidia-cuda-ubuntu-24.04
  disk_size_gb: 100
  rtlflow_version: "main"
  ```

#### 4.3 Dockerfiles
- [ ] 4.3.1. Create `dockerfiles/Dockerfile.sim` for RTL simulation
- [ ] 4.3.2. Create `dockerfiles/Dockerfile.synth` for RTL synthesis
- [ ] 4.3.3. Create `dockerfiles/Dockerfile.gpu` for GPU acceleration

#### 4.4 Build Infrastructure
- [ ] 4.4.1. Create ECR repositories for each RTL image
- [ ] 4.4.2. Create GitHub workflow `image_for_rtl_runners.yml`
- [ ] 4.4.3. Create Terraform for RTL image infrastructure
- [ ] 4.4.4. Add health checks for RTL runners

#### 4.5 Unit Tests for RTL Images
- [ ] 4.5.1. Test config YAML parsing for rtl-sim
- [ ] 4.5.2. Test config YAML parsing for rtl-synth
- [ ] 4.5.3. Test config YAML parsing for rtl-gpu
- [ ] 4.5.4. Test Dockerfile syntax validation
- [ ] 4.5.5. Test version extraction from configs

#### 4.6 Integration Tests for RTL Images
- [ ] 4.6.1. Test Docker image builds successfully
- [ ] 4.6.2. Test image push to ECR
- [ ] 4.6.3. Test image pull from ECR

#### 4.7 Documentation
- [ ] 4.7.1. Document RTL runner image build process

### Phase 5: EC2 Runner Infrastructure for RTL

#### 5.1 Launch Templates
- [ ] 5.1.1. Create launch template `rtl-sim-c8i`:
  - Instance type: c8i.4xlarge
  - AMI: Custom RTL sim image
  - Storage: 100 GB gp3
  - User data: Runner registration script
- [ ] 5.1.2. Create launch template `rtl-synth-r8i`:
  - Instance type: r8i.4xlarge
  - AMI: Custom RTL synth image
  - Storage: 200 GB gp3
- [ ] 5.1.3. Create launch template `rtl-gpu-g6e`:
  - Instance type: g6e.xlarge
  - AMI: Custom RTL GPU image
  - Storage: 100 GB gp3

#### 5.2 IAM and Security
- [ ] 5.2.1. Create IAM roles for RTL runners
- [ ] 5.2.2. Create security groups for RTL runners
- [ ] 5.2.3. Update VPC subnets if needed

#### 5.3 Scaling and Lifecycle
- [ ] 5.3.1. Create Auto Scaling groups (min 0, scale on demand)
- [ ] 5.3.2. Create Lambda for RTL runner lifecycle management
- [ ] 5.3.3. Add CloudWatch metrics for RTL runner utilization
- [ ] 5.3.4. Add cost allocation tags

#### 5.4 Unit Tests for EC2 Infrastructure
- [ ] 5.4.1. Test launch template generation
- [ ] 5.4.2. Test IAM policy document construction
- [ ] 5.4.3. Test security group rule validation
- [ ] 5.4.4. Test instance type validation (c8i, r8i, g6e only)
- [ ] 5.4.5. Test cost tag generation

#### 5.5 Integration Tests for EC2 Infrastructure
- [ ] 5.5.1. Test EC2 instance launch
- [ ] 5.5.2. Test runner registration with GitHub
- [ ] 5.5.3. Test runner termination on job complete

#### 5.6 E2E Tests for EC2 Infrastructure
- [ ] 5.6.1. Test full RTL simulation job on c8i
- [ ] 5.6.2. Test full RTL synthesis job on r8i

### Phase 6: RTL Simulation Endpoint

#### 6.1 API Design
- [ ] 6.1.1. Create `src/api/endpoints/rtl_simulation/` directory
- [ ] 6.1.2. Create API Lambda handler with endpoints:
  - `POST /v1/rtl-simulation` - Submit simulation job
  - `GET /v1/rtl-simulation/{job_id}` - Get job status
  - `GET /v1/rtl-simulation/{job_id}/results` - Get results
- [ ] 6.1.3. Create DynamoDB table for job tracking
- [ ] 6.1.4. Create S3 bucket for simulation artifacts

#### 6.2 Simulation Runner
- [ ] 6.2.1. Create simulation runner script:
  - Clone/update Chipyard
  - Build BOOM with tri-mode modifications
  - Run Verilator simulation
  - Upload results to S3
  - Update job status in DynamoDB
- [ ] 6.2.2. Add job timeout and cleanup
- [ ] 6.2.3. Add cost tracking per job

#### 6.3 Unit Tests for RTL Simulation
- [ ] 6.3.1. Test job submission validation
- [ ] 6.3.2. Test job ID generation
- [ ] 6.3.3. Test job status state machine
- [ ] 6.3.4. Test persona validation (riscv, desktop64, mobile64)
- [ ] 6.3.5. Test workload parameter validation
- [ ] 6.3.6. Test S3 artifact path generation
- [ ] 6.3.7. Test DynamoDB item construction
- [ ] 6.3.8. Test cost calculation logic
- [ ] 6.3.9. Test timeout detection
- [ ] 6.3.10. Test error response formatting

#### 6.4 Integration Tests for RTL Simulation
- [ ] 6.4.1. Test job submission to API
- [ ] 6.4.2. Test job status retrieval
- [ ] 6.4.3. Test S3 artifact upload/download
- [ ] 6.4.4. Test DynamoDB read/write

#### 6.5 E2E Tests for RTL Simulation
- [ ] 6.5.1. Test full simulation workflow (submit → poll → results)

#### 6.6 Frontend Updates
- [ ] 6.6.1. Update simulation UI to trigger real RTL simulations
- [ ] 6.6.2. Add job queue visualization
- [ ] 6.6.3. Add simulation progress tracking

### Phase 7: Tri-Mode Core Development

#### 7.1 Repository Setup
- [ ] 7.1.1. Fork Chipyard repository to 10U-Labs-LLC GitHub
- [ ] 7.1.2. Create branch for tri-mode modifications
- [ ] 7.1.3. Study BOOM frontend decode stage implementation

#### 7.2 Tri-Mode Decode Architecture
- [ ] 7.2.1. Design mode detection from instruction stream
- [ ] 7.2.2. Design Desktop64 decode lane
- [ ] 7.2.3. Design Mobile64 decode lane
- [ ] 7.2.4. Design unified micro-op emission to backend

#### 7.3 Implementation
- [ ] 7.3.1. Implement mode switching logic
- [ ] 7.3.2. Implement Desktop64 decoder stub
- [ ] 7.3.3. Implement Mobile64 decoder stub
- [ ] 7.3.4. Implement micro-op translation tables
- [ ] 7.3.5. Add flags speculation hardware
- [ ] 7.3.6. Add hardware TSO mode for Desktop64

#### 7.4 Unit Tests for Tri-Mode Core
- [ ] 7.4.1. Test mode detection logic
- [ ] 7.4.2. Test Desktop64 instruction decode
- [ ] 7.4.3. Test Mobile64 instruction decode
- [ ] 7.4.4. Test micro-op emission format
- [ ] 7.4.5. Test flags speculation hit/miss
- [ ] 7.4.6. Test TSO mode memory ordering

#### 7.5 Integration Tests for Tri-Mode Core
- [ ] 7.5.1. Run RISC-V compliance tests (native mode)
- [ ] 7.5.2. Measure IPC overhead vs. baseline BOOM

#### 7.6 Documentation
- [ ] 7.6.1. Document tri-mode architecture

### Phase 8: RTL Synthesis Pipeline

#### 8.1 API Design
- [ ] 8.1.1. Create `src/api/endpoints/rtl_synthesis/` directory
- [ ] 8.1.2. Create synthesis job API endpoint
- [ ] 8.1.3. Create synthesis job tracking in DynamoDB

#### 8.2 Synthesis Runner
- [ ] 8.2.1. Create synthesis runner script:
  - Take Verilog from simulation output
  - Run OpenLane flow
  - Generate timing/area reports
  - Generate GDSII
  - Upload artifacts to S3
- [ ] 8.2.2. Add DRC/LVS verification step

#### 8.3 Unit Tests for RTL Synthesis
- [ ] 8.3.1. Test synthesis job validation
- [ ] 8.3.2. Test Verilog input validation
- [ ] 8.3.3. Test OpenLane config generation
- [ ] 8.3.4. Test timing report parsing
- [ ] 8.3.5. Test area report parsing
- [ ] 8.3.6. Test DRC result parsing

#### 8.4 Integration Tests for RTL Synthesis
- [ ] 8.4.1. Test synthesis job submission
- [ ] 8.4.2. Test GDSII artifact download

#### 8.5 Frontend and Documentation
- [ ] 8.5.1. Create synthesis results dashboard
- [ ] 8.5.2. Document synthesis pipeline

### Phase 9: Frontend Updates

- [ ] 9.1. Update simulation UI to trigger real RTL simulations
- [ ] 9.2. Add job queue visualization
- [ ] 9.3. Add simulation progress tracking
- [ ] 9.4. Add waveform viewer (load VCD from S3)
- [ ] 9.5. Add synthesis results visualization
- [ ] 9.6. Add cost tracking display
- [ ] 9.7. Add architecture documentation pages
- [ ] 9.8. Add fabrication path documentation

### Phase 10: Fabrication Preparation

- [ ] 10.1. Research ChipFoundry.io submission requirements
- [ ] 10.2. Create GDSII validation pipeline
- [ ] 10.3. Create design rule check automation
- [ ] 10.4. Create submission package generator
- [ ] 10.5. Document fabrication process
- [ ] 10.6. Estimate fabrication cost and timeline
- [ ] 10.7. Create fabrication checklist

---

## File Changes Summary

### New Files

```
TODO.md (this file)
.github/workflow-order.yml
.github/workflows/check-dependencies.yml
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
