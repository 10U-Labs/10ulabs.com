# RTL Workflows

## Dependency Graph

```
ecs_runner.yml
    ↓
simulation_soc.yml (ECS on-demand)
```

---

## Task 1: Ensure simulation_soc.yml runs without problems

**Status:** Not started

**Uses:** ECS fargate on-demand

**Trigger:** `gh workflow run simulation_soc.yml`

---

## Notes

- simulation_soc.yml runs on ECS fargate on-demand only (no github_hosted support)
- Depends on ecs_runner.yml being operational
