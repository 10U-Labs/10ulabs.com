# Workflow Deployment - Atomic Task List

## Workflow Dependency Graph

```
bootstrap.yml
    ↓
www_shared.yml (github_hosted)
    ↓
api.yml (github_hosted)
    ↓
health.yml (github_hosted)
    ├──→ image_for_ec2_runners_endpoint.yml (github_hosted)
    │        ↓
    │    image_for_ec2_runners_post.yml (github_hosted)
    │        ↓
    │    runners.yml (github_hosted)
    │        ↓
    │    ec2_runner.yml (github_hosted) ────────────┐
    │                                               │
    └──→ ecr.yml (github_hosted)                    │
             ↓                                      │
         image_for_ecs_runners.yml (github_hosted)  │
             ↓                                      │
         ecs_runner.yml (github_hosted) ←───────────┘
             ↓
             ├──→ contact.yml (ECS on-demand)
             │        ↓
             │    www_index.yml (ECS on-demand)
             │
             ├──→ echo.yml (ECS on-demand)
             └──→ rack_designer.yml (ECS on-demand)
```

See RTL.md for simulation_soc.yml.

---

## Tasks

- [x] Task 1: Ensure bootstrap.yml runs without problems
- [x] Task 2: Ensure www_shared.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run www_shared.yml --field github_hosted=true`
- [ ] Task 3: Ensure api.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run api.yml --field github_hosted=true`
- [ ] Task 4: Ensure health.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run health.yml --field github_hosted=true`
- [ ] Task 5: Ensure image_for_ec2_runners_endpoint.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ec2_runners_endpoint.yml --field github_hosted=true`
- [ ] Task 6: Ensure image_for_ec2_runners_post.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ec2_runners_post.yml --field github_hosted=true`
- [ ] Task 7: Ensure runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run runners.yml --field github_hosted=true`
- [ ] Task 8: Ensure ec2_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ec2_runner.yml --field github_hosted=true`
- [ ] Task 9: Ensure ecr.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ecr.yml --field github_hosted=true`
- [ ] Task 10: Ensure image_for_ecs_runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ecs_runners.yml --field github_hosted=true`
- [ ] Task 11: Ensure ecs_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ecs_runner.yml --field github_hosted=true`
- [ ] Task 12: Ensure contact.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run contact.yml`
- [ ] Task 13: Ensure echo.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run echo.yml`
- [ ] Task 14: Ensure rack_designer.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run rack_designer.yml`
- [ ] Task 15: Ensure www_index.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run www_index.yml`
- [ ] Task 16: STOP AND ASK USER for next steps

---

## Notes

- Workflows up to and including ecs_runner.yml support `github_hosted=true` and `[github-hosted]`
- Workflows after ecs_runner.yml run on ECS fargate on-demand only
- Complete each task fully before starting the next
