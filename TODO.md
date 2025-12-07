# Workflow Deployment - Atomic Task List

## Workflow Dependency Graph

```
bootstrap.yml
    ↓
www_shared.yml (github_hosted)
    ↓
api_backend.yml (github_hosted)
    ↓
endpoint_health.yml (github_hosted)
    ├──→ endpoint_v1_image_for_ec2_runners.yml (github_hosted)
    │        ↓
    │    endpoint_v1_image_for_ec2_runners_post.yml (github_hosted)
    │        ↓
    │    endpoint_v1_runners.yml (github_hosted)
    │        ↓
    │    endpoint_v1_ec2_runner.yml (github_hosted) ────────────┐
    │                                               │
    └──→ api_shared_ecr.yml (github_hosted) ───────────────────┤
                                                    ↓
                            endpoint_v1_image_for_ecs_runners.yml (github_hosted)
                                                    ↓
                            endpoint_v1_ecs_runner.yml (github_hosted)
                                                    ↓
             ├──→ endpoint_v1_contact.yml (ECS on-demand)
             │        ↓
             │    www_index.yml (ECS on-demand)
             │
             ├──→ endpoint_v1_echo.yml (ECS on-demand)
             └──→ endpoint_v1_rack_designer.yml (ECS on-demand)
```

See RTL.md for endpoint_v1_simulation_soc.yml.

---

## Tasks

- [x] Task 1: Ensure bootstrap.yml runs without problems
- [x] Task 2: Ensure www_shared.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run www_shared.yml --field github_hosted=true`
- [x] Task 3: Ensure api_backend.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run api_backend.yml --field github_hosted=true`
- [x] Task 4: Ensure endpoint_health.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_health.yml --field github_hosted=true`
- [ ] Task 5: Ensure endpoint_v1_image_for_ec2_runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_image_for_ec2_runners.yml --field github_hosted=true`
- [ ] Task 6: Ensure endpoint_v1_image_for_ec2_runners_post.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_image_for_ec2_runners_post.yml --field github_hosted=true`
- [ ] Task 7: Ensure endpoint_v1_runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_runners.yml --field github_hosted=true`
- [ ] Task 8: Ensure endpoint_v1_ec2_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_ec2_runner.yml --field github_hosted=true`
- [ ] Task 9: Ensure api_shared_ecr.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run api_shared_ecr.yml --field github_hosted=true`
- [ ] Task 10: Ensure endpoint_v1_image_for_ecs_runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_image_for_ecs_runners.yml --field github_hosted=true`
- [ ] Task 11: Ensure endpoint_v1_ecs_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run endpoint_v1_ecs_runner.yml --field github_hosted=true`
- [ ] Task 12: Ensure endpoint_v1_contact.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run endpoint_v1_contact.yml`
- [ ] Task 13: Ensure endpoint_v1_echo.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run endpoint_v1_echo.yml`
- [ ] Task 14: Ensure endpoint_v1_rack_designer.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run endpoint_v1_rack_designer.yml`
- [ ] Task 15: Ensure www_index.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run www_index.yml`
- [ ] Task 16: STOP AND ASK USER for next steps

---

## Notes

- Workflows up to and including endpoint_v1_ecs_runner.yml support `github_hosted=true` and `[github-hosted]`
- Workflows after endpoint_v1_ecs_runner.yml run on ECS fargate on-demand only
- Complete each task fully before starting the next
