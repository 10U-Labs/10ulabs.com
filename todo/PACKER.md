# Packer Contribution Plan

Proposed PRs for [hashicorp/packer-plugin-amazon](https://github.com/hashicorp/packer-plugin-amazon) to add on-demand instance failover capabilities.

## Background

Packer's amazon-ebs builder supports multiple instance types for spot instances via `spot_instance_types`, which uses EC2 Fleet under the hood. However, on-demand instances only support a single `instance_type` with no failover mechanism for capacity errors.

Our use case: building AMIs for GitHub Actions runners using on-demand instances with automatic failover across multiple subnets/AZs when `InsufficientInstanceCapacity` errors occur.

## Proposed PRs

### PR 1: Add `on_demand_instance_types` parameter

**Goal:** Allow specifying multiple instance types for on-demand builds, similar to `spot_instance_types`.

**Changes:**
- Add `on_demand_instance_types` parameter to the EBS builder config
- Use EC2 Fleet API with `DefaultTargetCapacityType: "on-demand"` when multiple types specified
- Build fleet overrides for all specified instance types
- Mutually exclusive with `instance_type` (same pattern as `spot_instance_types`)

**Example config:**
```hcl
source "amazon-ebs" "example" {
  on_demand_instance_types = ["m6i.large", "m5.large", "m6a.large"]
  # ... other config
}
```

**Related issues:**
- https://github.com/hashicorp/packer/issues/3924 (closed wontfix in 2017, but only for spot)

---

### PR 2: Add `subnet_ids` parameter for multi-subnet failover

**Goal:** Allow specifying multiple subnets so EC2 Fleet can try different AZs on capacity errors.

**Changes:**
- Add `subnet_ids` parameter (list of subnet IDs)
- When used with Fleet API, build overrides for all subnet × instance type combinations
- Mutually exclusive with `subnet_id` and `subnet_filter`

**Example config:**
```hcl
source "amazon-ebs" "example" {
  on_demand_instance_types = ["m6i.large", "m5.large"]
  subnet_ids = ["subnet-abc123", "subnet-def456", "subnet-ghi789"]
  # ... other config
}
```

---

### PR 3: Add `subnet_filter` support for multiple subnets

**Goal:** Extend `subnet_filter` to work with Fleet API when multiple subnets match.

**Changes:**
- Remove the "exactly one subnet" requirement when using Fleet mode
- Add `allow_multiple` option to `subnet_filter`
- When multiple subnets match and Fleet mode is active, use all matching subnets as overrides

**Example config:**
```hcl
source "amazon-ebs" "example" {
  on_demand_instance_types = ["m6i.large", "m5.large"]
  subnet_filter {
    filters = {
      "tag:Environment": "build"
    }
    allow_multiple = true
  }
  # ... other config
}
```

**Related issues:**
- https://github.com/hashicorp/packer/issues/2485 (closed wontfix - AZ selection)

---

### PR 4: Add `fleet_allocation_strategy` for on-demand

**Goal:** Allow configuring the on-demand allocation strategy when using Fleet API.

**Changes:**
- Add `fleet_allocation_strategy` parameter
- Support values: `lowest-price`, `prioritized`
- Default to `lowest-price` for cost optimization

**Example config:**
```hcl
source "amazon-ebs" "example" {
  on_demand_instance_types = ["m6i.large", "m5.large"]
  fleet_allocation_strategy = "lowest-price"
  # ... other config
}
```

---

### PR 5: Wait and poll EC2 instance status

**Goal:** After launching an instance via Fleet API, properly wait for and poll the EC2 instance status before proceeding with provisioning.

**Changes:**
- Add polling logic to wait for instance to reach `running` state after Fleet creation
- Handle instance status checks (system status, instance status)
- Implement configurable timeout and polling interval
- Surface meaningful errors when instance fails to reach ready state

**Example config:**
```hcl
source "amazon-ebs" "example" {
  on_demand_instance_types = ["m6i.large", "m5.large"]
  # ... other config
}
```

---

## Implementation Notes

### EC2 Fleet API usage

The key is using `create_fleet` with `Type: "instant"` and on-demand target capacity:

```go
CreateFleetInput{
    Type: "instant",
    TargetCapacitySpecification: {
        TotalTargetCapacity: 1,
        DefaultTargetCapacityType: "on-demand",
    },
    OnDemandOptions: {
        AllocationStrategy: "lowest-price",
    },
    LaunchTemplateConfigs: [{
        LaunchTemplateSpecification: {...},
        Overrides: [
            // All combinations of instance types × subnets
            {InstanceType: "m6i.large", SubnetId: "subnet-abc"},
            {InstanceType: "m6i.large", SubnetId: "subnet-def"},
            {InstanceType: "m5.large", SubnetId: "subnet-abc"},
            {InstanceType: "m5.large", SubnetId: "subnet-def"},
        ],
    }],
}
```

### Files to modify

In `packer-plugin-amazon`:
- `builder/ebs/builder.go` - main builder logic
- `builder/common/run_config.go` - config parameters
- `builder/common/step_run_source_instance.go` - instance launch logic
- `builder/common/step_run_spot_instance.go` - reference for Fleet API usage

### Testing considerations

- Unit tests for config validation (mutual exclusivity)
- Acceptance tests with multiple subnets across AZs
- Test capacity error handling when some AZs lack capacity

## References

- Our implementation: `lib/python/ec2_fleet/ec2_fleet.py`
- Packer spot implementation: uses Fleet API already for `spot_instance_types`
- EC2 Fleet docs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet.html
