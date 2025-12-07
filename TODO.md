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

- [x] Task 1: Ensure `bootstrap.yml` runs without problems
- [x] Task 2: Ensure `www_shared.yml` runs without problems
- [x] Task 3: Ensure `api_backend.yml` runs without problems
- [x] Task 4: Ensure `endpoint_health.yml` runs without problems
- [ ] Task 5: Ensure `endpoint_v1_image_for_ec2_runners.yml` runs without problems
- [ ] Task 6: Ensure `endpoint_v1_image_for_ec2_runners_post.yml` runs without problems
- [ ] Task 7: Ensure `endpoint_v1_runners.yml` runs without problems
- [ ] Task 8: Ensure `endpoint_v1_ec2_runner.yml` runs without problems
- [ ] Task 9: Ensure `api_shared_ecr.yml` runs without problems
- [ ] Task 10: Ensure `endpoint_v1_image_for_ecs_runners.yml` runs without problems
- [ ] Task 11: Ensure `endpoint_v1_ecs_runner.yml` runs without problems
- [ ] Task 12: Ensure `endpoint_v1_contact.yml` runs without problems
- [ ] Task 13: Ensure `endpoint_v1_echo.yml` runs without problems
- [ ] Task 14: Ensure `endpoint_v1_rack_designer.yml` runs without problems
- [ ] Task 15: Ensure `www_index.yml` runs without problems
