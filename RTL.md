# RTL Workflows

## Dependency Graph

```
endpoint_v1_ecs_runner.yml
    ↓
endpoint_v1_simulation_soc.yml (ECS on-demand)
```

---

## Task 1: Ensure endpoint_v1_simulation_soc.yml runs without problems

**Status:** Not started

**Uses:** ECS fargate on-demand

**Trigger:** `gh workflow run endpoint_v1_simulation_soc.yml`

---

## Notes

- endpoint_v1_simulation_soc.yml runs on ECS fargate on-demand only (no github_hosted support)
- Depends on endpoint_v1_ecs_runner.yml being operational
