# Runner Label System

This document describes the composable runner label system for GitHub Actions self-hosted runners.

## Overview

The label system uses composable labels to select the appropriate runner infrastructure. Labels are parsed from job definitions and used to determine:
- **Platform**: ECS (containerized) or EC2 (bare metal)
- **Compute**: Instance type or Fargate configuration
- **Pricing**: Spot or on-demand capacity

## Label Schema

```
Platform:     ecs | ec2
Compute:      fargate | c8i | r8i | g6e
Pricing:      spot | on-demand
Runner ID:    runner-{github.run_id}
```

### Required Labels

Every job must include:
1. One **platform** label (`ecs` or `ec2`)
2. One **compute** label (matching the platform)
3. One **pricing** label (`spot` or `on-demand`)
4. One **runner ID** label (`runner-NNNN` where NNNN is the workflow run ID)

### Valid Combinations

| Platform | Compute   | Pricing     | Instance Type   | Use Case |
|----------|-----------|-------------|-----------------|----------|
| ecs      | fargate   | spot        | N/A (Fargate)   | Cost-optimized CI/CD |
| ecs      | fargate   | on-demand   | N/A (Fargate)   | Reliable CI/CD |
| ec2      | c8i       | spot        | c8i.4xlarge     | Cost-optimized compute |
| ec2      | c8i       | on-demand   | c8i.4xlarge     | RTL simulation |
| ec2      | r8i       | on-demand   | r8i.4xlarge     | RTL synthesis |
| ec2      | g6e       | on-demand   | g6e.xlarge      | GPU acceleration |

### Invalid Combinations

These combinations will be rejected:
- `ecs` + `c8i` (c8i is an EC2 instance type)
- `ecs` + `r8i` (r8i is an EC2 instance type)
- `ecs` + `g6e` (g6e is an EC2 instance type)
- `ec2` + `fargate` (fargate is an ECS capacity type)

## Usage in Workflows

### ECS Fargate Runner (Spot)

```yaml
jobs:
  build:
    runs-on:
      - ecs
      - fargate
      - spot
      - runner-${{ github.run_id }}
```

### EC2 c8i Runner (On-Demand)

```yaml
jobs:
  rtl-simulation:
    runs-on:
      - ec2
      - c8i
      - on-demand
      - runner-${{ github.run_id }}
```

### EC2 r8i Runner (On-Demand)

```yaml
jobs:
  rtl-synthesis:
    runs-on:
      - ec2
      - r8i
      - on-demand
      - runner-${{ github.run_id }}
```

### EC2 g6e Runner (On-Demand)

```yaml
jobs:
  gpu-batch:
    runs-on:
      - ec2
      - g6e
      - on-demand
      - runner-${{ github.run_id }}
```

## Label Processing Flow

```
GitHub Webhook → Webhook Router → Parse Labels → Validate → Route to Handler
                      ↓
              ┌───────────────┐
              │ get_runner_   │
              │ type_from_    │
              │ labels()      │
              └───────────────┘
                      ↓
         ┌───────────────────────┐
         │ parse_labels()        │
         │ - Extract platform    │
         │ - Extract compute     │
         │ - Extract pricing     │
         │ - Extract runner_id   │
         └───────────────────────┘
                      ↓
         ┌───────────────────────┐
         │ validate_labels()     │
         │ - Check valid combo   │
         │ - Reject invalid      │
         └───────────────────────┘
                      ↓
    ┌────────────────┴────────────────┐
    ↓                                 ↓
┌─────────┐                     ┌─────────┐
│  ECS    │                     │  EC2    │
│ Handler │                     │ Handler │
└─────────┘                     └─────────┘
    ↓                                 ↓
┌─────────────────┐           ┌─────────────────┐
│ get_capacity_   │           │ get_instance_   │
│ provider()      │           │ type()          │
│ FARGATE/        │           │ c8i.4xlarge/    │
│ FARGATE_SPOT    │           │ r8i.4xlarge/    │
└─────────────────┘           │ g6e.xlarge      │
                              └─────────────────┘
```

## API Reference

### `lib/python/runner_labels.py`

#### `parse_labels(labels: List[str]) -> ParsedLabels`

Parse a list of job labels into a structured `ParsedLabels` object.

**Raises**: `LabelParseError` if required labels are missing.

#### `validate_labels(parsed: ParsedLabels) -> None`

Validate that a parsed label combination is valid.

**Raises**: `LabelValidationError` for invalid combinations.

#### `get_instance_type(parsed: ParsedLabels) -> str | None`

Get the EC2 instance type for a parsed label set.

**Returns**: Instance type string (e.g., `c8i.4xlarge`) or `None` for ECS.

#### `is_spot(parsed: ParsedLabels) -> bool`

Check if the pricing label indicates spot pricing.

**Returns**: `True` if pricing is `spot`, `False` if `on-demand`.

#### `get_ecs_config(parsed: ParsedLabels) -> Dict | None`

Get ECS task configuration for a parsed label set.

**Returns**: Dict with `cpu` and `memory` keys, or `None` for EC2.

## Backwards Compatibility

The webhook router maintains backwards compatibility with legacy labels through environment variables:
- `RUNNER_LABEL_EC2`
- `RUNNER_LABEL_EC2_E2E`
- `RUNNER_LABEL_FARGATE`
- `RUNNER_LABEL_FARGATE_E2E`

If new-format labels cannot be parsed, the router falls back to checking for these legacy labels.

## Testing

Unit tests: `test/lib/test_runner_labels.py`
Integration tests: `test/api/endpoints/runners/post_deployment/integration/test_label_system.py`

```bash
# Run unit tests
pytest test/lib/test_runner_labels.py -v

# Run integration tests
pytest test/api/endpoints/runners/post_deployment/integration/test_label_system.py -v
```
